use serde::{Deserialize, Serialize};
use solana_sdk::signature::Signature;
use std::env;
use std::path::PathBuf;

#[derive(Deserialize, Serialize)]
pub struct DevPayResponse {
    pub signature: Signature,
    pub status_code: u16,
}

#[derive(Deserialize, Serialize)]
pub struct PayTransaction {
    pub transaction_url: String,
    pub qr_code: String,
}

pub fn get_parent_app() -> PathBuf {
    let dir = env::current_dir().expect("Failed to get current directory");
    let parent_app = dir
        .ancestors()
        .nth(2)
        .expect("Failed to get to parent app directory");
    PathBuf::from(parent_app)
}

pub fn load_env() {
    let parent_app = get_parent_app();
    let env_path = parent_app.join("../../../../.env.shared");
    println!("env = {}", env_path.display());
    dotenvy::from_path(&env_path).expect("Failed to load .env.shared file")
}

#[derive(Default)]
pub enum Backend {
    #[default]
    Dev,
    Pay,
    QrPay,
}

pub fn build_backend(kind: Backend) -> String {
    let domain = env::var("DOMAIN").expect("Expected DOMAIN variable");
    let port = env::var("PORT_RUST").expect("Expected PORT_RUST variable");
    let dev_pay = env::var("DEV_PAY").expect("Expected DEV_PAY variable");
    let pay = env::var("PAY").expect("Expected PAY variable");
    let qr_pay = env::var("QR_PAY").expect("Expected QR_PAY variable");

    format!("{}:{}{}", domain, port, {
        match kind {
            Backend::Dev => dev_pay,
            Backend::Pay => pay,
            Backend::QrPay => qr_pay,
        }
    })
}
