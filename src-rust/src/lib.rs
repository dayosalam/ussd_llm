use crate::prelude::ClusterURL;
use anchor_client::solana_client::rpc_client::RpcClient;
use base64::alphabet::STANDARD;
use base64::engine::{GeneralPurpose, GeneralPurposeConfig};
use solana_sdk::commitment_config::CommitmentConfig;
use std::ops::Deref;
use std::path::PathBuf;
use std::sync::{Arc, LazyLock};
use std::{env, fs};

pub mod server;

pub const ENV: LazyLock<()> = LazyLock::new(|| {
    let dir = env::current_dir().expect("Expected to find current working directory");
    let parent_dir = dir.parent().expect("Expected to find parent directory");
    let env_path = parent_dir.join("../../.env.shared");
    dotenvy::from_path(env_path).expect("Environment variables did not load successfully");
});
pub fn get_env(key: &str) -> String {
    let _ = ENV.deref();
    env::var(key).expect(&format!("Couldn't find key '{}' in .env.shared", key))
}
pub const PORT_RUST: LazyLock<String> = LazyLock::new(|| get_env("PORT_RUST"));
pub const PORT_APP: LazyLock<String> = LazyLock::new(|| get_env("PORT_APP"));
pub const DOMAIN: LazyLock<String> = LazyLock::new(|| get_env("DOMAIN"));
pub const HOME: LazyLock<String> = LazyLock::new(|| get_env("HOME"));
pub const PAY: LazyLock<String> = LazyLock::new(|| get_env("PAY"));
pub const QR_PAY: LazyLock<String> = LazyLock::new(|| get_env("QR_PAY"));
pub const DEV_PAY: LazyLock<String> = LazyLock::new(|| get_env("DEV_PAY"));
pub const TX: LazyLock<String> = LazyLock::new(|| get_env("TX"));
pub const CLUSTER: LazyLock<String> = LazyLock::new(|| get_env("CLUSTER"));

pub const DEV_SENDER: LazyLock<[u8; 64]> = LazyLock::new(|| {
    let sender_path = PathBuf::from("/home/chijioke_joseph/.config/solana/id.json");
    let file_str = fs::read_to_string(&sender_path).expect("Failed to read sender keypair file");
    let file_bytes =
        serde_json::from_str::<Vec<u8>>(&file_str).expect("Failed to parse sender keypair file");
    let mut byte_array = [0u8; 64];
    byte_array.copy_from_slice(&file_bytes);
    byte_array
});

pub struct AppState {
    pub client: RpcClient,
    pub base64_encoder: GeneralPurpose,
}

pub const STATE: LazyLock<Arc<AppState>> = LazyLock::new(|| {
    Arc::new(AppState {
        client: RpcClient::new_with_commitment(
            (
                match CLUSTER.deref() as &str {
                    "mainnet" => ClusterURL::Mainnet,
                    "testnet" => ClusterURL::Testnet,
                    "devnet" => ClusterURL::Devnet,
                    _ => {
                        eprintln!("invalid cluster specified. value {} is not among ['mainnet', 'testnet', 'devnet']", CLUSTER.deref());
                        std::process::exit(1);
                    }
                }
            ).resolve(),
            CommitmentConfig::confirmed(),
        ),
        base64_encoder: GeneralPurpose::new(&STANDARD, GeneralPurposeConfig::default()),
    })
});

pub mod prelude {
    pub use crate::server::utils::{ClusterURL, KeypairWrapper};
    pub use crate::server::{handle_dev_pay, handle_post_pay, handle_qr_pay, PayRequest};
    pub use crate::AppState;
    pub use crate::{
        CLUSTER, DEV_PAY, DEV_SENDER, DOMAIN, PAY, PORT_APP, PORT_RUST, QR_PAY, STATE, TX,
    };
}
