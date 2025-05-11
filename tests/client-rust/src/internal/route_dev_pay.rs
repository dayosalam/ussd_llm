use crate::internal::utils::{build_backend, load_env, Backend, DevPayResponse};
use std::collections::HashMap;
use std::env;

pub async fn dev_pay() {
    load_env();
    let url = build_backend(Backend::Dev);
    println!("url = {url}");
    let cluster = env::var("CLUSTER").expect("Expected CLUSTER variable");
    let (cmd, name): (_, &str) = match &cluster as &str {
        "mainnet" => ('m', &cluster),
        "testnet" => ('t', &cluster),
        "devnet" => ('d', &cluster),
        _ => {
            eprintln!("Invalid cluster specified");
            return;
        }
    };
    let client = reqwest::Client::new();
    let body = HashMap::from([
        (
            "recipient",
            serde_json::json!("HwQjbdYzDPCdY19ZbCecsvk8av6o6xKjnv33LGcsbNSL"),
        ),
        ("amount", serde_json::json!(0.01)),
    ]);
    let result = client
        .post(&url)
        .header("Content-Type", "application/json")
        .json(&body)
        .send()
        .await;
    let response = match result {
        Ok(val) => val,
        Err(e) => {
            eprintln!("Request failed due to error {e:?}");
            return;
        }
    };
    let resp_body = match response.json::<DevPayResponse>().await {
        Ok(val) => val,
        Err(e) => {
            eprintln!("Parsing response body failed due to error {e:?}");
            return;
        }
    };
    let command = format!("solana confirm {} -u{cmd}", resp_body.signature.to_string());
    println!("{name} transfer successful. Run the following command below to view the details");
    println!("{command}");
}
