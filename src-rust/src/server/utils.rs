use anchor_client::solana_client::rpc_client::RpcClient;
use axum::http::StatusCode;
use base64::engine::GeneralPurpose;
use base64::Engine;
use image::{ImageFormat, Luma};
use qrcode::QrCode;
use solana_sdk::native_token::sol_to_lamports;
use solana_sdk::pubkey::Pubkey;
use solana_sdk::signature::Keypair;
use std::io::Cursor;
use std::ops::{Deref, DerefMut};
use std::str::FromStr;

pub struct KeypairWrapper(Keypair);

impl KeypairWrapper {
    pub fn new() -> Self {
        Self(Keypair::new())
    }
    pub fn swap(&mut self, new_key: Keypair) {
        self.0 = new_key;
    }
}

impl Deref for KeypairWrapper {
    type Target = Keypair;
    fn deref(&self) -> &Self::Target {
        &self.0
    }
}

impl DerefMut for KeypairWrapper {
    fn deref_mut(&mut self) -> &mut Self::Target {
        &mut self.0
    }
}

#[derive(Debug)]
pub enum ClusterURL {
    Mainnet,
    Testnet,
    Devnet,
}

impl ClusterURL {
    pub fn resolve(&self) -> &'static str {
        match self {
            ClusterURL::Mainnet => "https://api.mainnet-beta.solana.com",
            ClusterURL::Devnet => "https://api.devnet.solana.com",
            ClusterURL::Testnet => "https://api.testnet.solana.com",
        }
    }
}

pub fn check_balance(
    client: &RpcClient,
    sender: Option<&str>,
    amount: f64,
) -> Result<bool, String> {
    let sender = sender.ok_or("Sender not specified".to_string())?;
    let sender = Pubkey::from_str(sender)
        .map_err(|e| format!("Failed to get sender's public key due to error {e}"))?;
    let balance = client
        .get_balance(&sender)
        .map_err(|e| format!("Failed to get sender's balance due to error {e}"))?;
    let amount = sol_to_lamports(amount);
    println!("sender_pubkey = {}", sender.to_string());
    Ok(balance >= amount)
}

pub fn create_pay_url(
    recipient: &Pubkey,
    amount: f64,
    reference: &Pubkey,
    label: Option<&str>,
    message: Option<&str>,
) -> String {
    fn access(val: Option<&str>, url_param_name: &str) -> String {
        match val {
            Some(val) => format!("&{url_param_name}={}", urlencoding::encode(val)),
            None => "".to_string(),
        }
    }
    let sign_url = format!(
        "solana:{}?amount={}&reference={}{}{}",
        recipient.to_string(),
        amount,
        reference.to_string(),
        access(label, "label"),
        access(message, "message")
    );
    sign_url
}

pub fn generate_qr_code(
    data: &str,
    encoder: &GeneralPurpose,
) -> Result<String, (StatusCode, String)> {
    let qr = QrCode::new(data.as_bytes()).map_err(|e| {
        (
            StatusCode::INTERNAL_SERVER_ERROR,
            format!("Failed to generate qr code due to error {e}"),
        )
    })?;
    let image = qr.render::<Luma<u8>>().quiet_zone(false).build();
    let mut bytes = Vec::new();
    image
        .write_to(&mut Cursor::new(&mut bytes), ImageFormat::Png)
        .map_err(|e| {
            (
                StatusCode::INTERNAL_SERVER_ERROR,
                format!("Failed to write image bytes to buffer due to error {e}"),
            )
        })?;
    Ok(encoder.encode(&bytes))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::server::REFERENCE_KEYPAIR;
    use solana_sdk::signer::Signer;
    use std::str::FromStr;

    pub struct Data {
        recipient: Pubkey,
        amount: f64,
        label: String,
        message: String,
        expected: String,
    }

    impl Data {
        pub fn new() -> Self {
            Self {
                recipient: Pubkey::from_str("mvines9iiHiQTysrwkJjGf2gb9Ex9jXJX8ns3qwf2kN").unwrap(),
                amount: 1f64,
                label: String::from("Michael"),
                message: String::from("Thanks for all the fish"),
                expected: format!(
                    "solana:mvines9iiHiQTysrwkJjGf2gb9Ex9jXJX8ns3qwf2kN?amount=1&reference={}&label=Michael&message=Thanks%20for%20all%20the%20fish",
                    REFERENCE_KEYPAIR
                        .deref()
                        .lock()
                        .unwrap()
                        .pubkey()
                        .to_string()
                ),
            }
        }
    }

    #[test]
    fn test_create_pay_url() {
        let data = Data::new();
        let reference = REFERENCE_KEYPAIR.deref().lock().unwrap();
        let url = create_pay_url(
            &data.recipient,
            data.amount,
            &reference.pubkey(),
            Some(&data.label),
            Some(&data.message),
        );
        println!("solana pay url = {}", url);
        assert_eq!(&url, &data.expected);
    }
}
