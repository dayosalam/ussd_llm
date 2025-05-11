pub mod utils;

use crate::server::utils::{check_balance, create_pay_url, generate_qr_code, KeypairWrapper};
use axum::http::StatusCode;
use axum::Json;
use base64::Engine;
use serde::{Deserialize, Serialize};
use solana_sdk::system_instruction;
use std::ops::Deref;
use std::str::FromStr;
use std::sync::{Arc, LazyLock, Mutex};

#[derive(Deserialize, Serialize)]
pub struct PayRequest {
    pub sender: Option<String>,
    pub recipient: String,
    pub label: Option<String>,
    pub message: Option<String>,
    pub amount: f64,
}

pub static REFERENCE_KEYPAIR: LazyLock<Arc<Mutex<KeypairWrapper>>> =
    LazyLock::new(|| Arc::new(Mutex::new(KeypairWrapper::new())));

#[derive(Deserialize, Serialize)]
pub struct DevPayRequest {
    pub recipient: String,
    pub amount: f64,
}

#[derive(Deserialize, Serialize)]
pub struct PayTransaction {
    pub transaction_url: String,
    pub reference: String,
    pub qr_code: String,
}

#[derive(Deserialize, Serialize)]
pub struct PayResponse {
    pub auth_url: String,
    pub status_code: u16,
}

#[derive(Deserialize, Serialize)]
pub struct DevPayResponse {
    pub signature: Signature,
    pub status_code: u16,
}

use crate::{AppState, DEV_SENDER, DOMAIN, PORT_APP, TX};
use axum::extract::State;
use solana_sdk::native_token::sol_to_lamports;
use solana_sdk::pubkey::Pubkey;
use solana_sdk::signature::{Keypair, Signature};
use solana_sdk::signer::Signer;
use solana_sdk::transaction::Transaction;

pub async fn handle_qr_pay(
    State(state): State<Arc<AppState>>,
    Json(req): Json<PayRequest>,
) -> Result<Json<PayTransaction>, (StatusCode, String)> {
    let PayRequest {
        amount,
        recipient,
        label,
        message,
        sender,
    } = req;
    let state = state.deref();
    let AppState {
        base64_encoder,
        client,
    } = state;
    let recipient_key = Pubkey::from_str(&recipient).map_err(|_| {
        (
            StatusCode::BAD_REQUEST,
            "Invalid recpient pubkey".to_string(),
        )
    })?;

    let check = check_balance(client, sender.as_ref().map(|x| x as &str), amount);
    match check {
        Ok(val) => val.then(|| ()).ok_or((
            StatusCode::BAD_REQUEST,
            "Sender does not have sufficient balance to complete the transaction with its fees."
                .to_string(),
        ))?,
        Err(_) => (),
    }

    let reference = Keypair::new();

    let sign_url = create_pay_url(
        &recipient_key,
        amount,
        &reference.pubkey(),
        label.as_ref().map(|x| x as &str),
        message.as_ref().map(|x| x as &str),
    );
    let qr_code = generate_qr_code(&sign_url, base64_encoder)?;
    REFERENCE_KEYPAIR.deref().lock().unwrap().swap(reference);

    Ok(Json(PayTransaction {
        transaction_url: sign_url,
        reference: REFERENCE_KEYPAIR
            .deref()
            .lock()
            .unwrap()
            .pubkey()
            .to_string(),
        qr_code,
    }))
}

pub async fn handle_post_pay(
    State(state): State<Arc<AppState>>,
    Json(req): Json<PayRequest>,
) -> Result<Json<PayResponse>, (StatusCode, String)> {
    let PayRequest {
        amount,
        sender,
        recipient,
        ..
    } = req;
    let state = state.deref();
    let AppState {
        base64_encoder,
        client,
    } = state;
    let sender_key = Pubkey::from_str(sender.as_ref().unwrap())
        .map_err(|_| (StatusCode::BAD_REQUEST, "Invalid sender pubkey".to_string()))?;
    let recipient_key = Pubkey::from_str(&recipient).map_err(|_| {
        (
            StatusCode::BAD_REQUEST,
            "Invalid recipient pubkey".to_string(),
        )
    })?;
    let check = check_balance(client, sender.as_ref().map(|x| x as &str), amount);
    match check {
        Ok(val) => val.then(|| ()).ok_or((
            StatusCode::BAD_REQUEST,
            "The sender does not have enough lamports to complete the transaction".to_string(),
        ))?,
        Err(_) => (),
    }
    let amount = sol_to_lamports(amount);

    let instruction = system_instruction::transfer(&sender_key, &recipient_key, amount);
    let transaction = Transaction::new_with_payer(&[instruction], Some(&sender_key));
    let tx =
        bincode::serde::encode_to_vec(&transaction, bincode::config::standard()).map_err(|e| {
            (
                StatusCode::INTERNAL_SERVER_ERROR,
                format!("Failed to serialize transaction due to error: {e}"),
            )
        })?;
    let encoded_tx = base64_encoder.encode(&tx);
    let auth_url = format!(
        "{}:{}/?{}={}",
        DOMAIN.deref(),
        PORT_APP.deref(),
        TX.deref(),
        encoded_tx
    );
    let response = Json(PayResponse {
        auth_url,
        status_code: StatusCode::OK.as_u16(),
    });
    Ok(response)
}

pub async fn handle_dev_pay(
    State(state): State<Arc<AppState>>,
    Json(req): Json<DevPayRequest>,
) -> Result<Json<DevPayResponse>, (StatusCode, String)> {
    let state = state.deref();
    let AppState { client, .. } = state;
    let DevPayRequest { recipient, amount } = req;
    let sender = Keypair::from_bytes(DEV_SENDER.deref() as &[u8]).map_err(|e| {
        (
            StatusCode::INTERNAL_SERVER_ERROR,
            format!("Failed to initialize development server sender due to error {e}"),
        )
    })?;
    let check = check_balance(client, Some(&sender.pubkey().to_string()), amount);
    match check {
        Ok(val) => val.then(|| ()).ok_or((
            StatusCode::BAD_REQUEST,
            "The sender does not have enough lamports to complete the transaction".to_string(),
        ))?,
        Err(_) => (),
    }

    let amount = sol_to_lamports(amount);
    let recipient_key = Pubkey::from_str(&recipient).map_err(|_| {
        (
            StatusCode::BAD_REQUEST,
            "Invalid recipient pubkey".to_string(),
        )
    })?;
    let recent_blockhash = client.get_latest_blockhash().map_err(|e| {
        (
            StatusCode::INTERNAL_SERVER_ERROR,
            format!("Failed to get the most recent block hash on the block chain due to error {e}"),
        )
    })?;
    let instruction = system_instruction::transfer(&sender.pubkey(), &recipient_key, amount);
    let transaction = Transaction::new_signed_with_payer(
        &[instruction],
        Some(&sender.pubkey()),
        &[sender],
        recent_blockhash,
    );
    let signature = client
        .send_and_confirm_transaction(&transaction)
        .map_err(|e| {
            (
                StatusCode::EXPECTATION_FAILED,
                format!("Failed to confirm transaction request due to error {e}"),
            )
        })?;

    Ok(Json(DevPayResponse {
        signature,
        status_code: StatusCode::OK.as_u16(),
    }))
}
