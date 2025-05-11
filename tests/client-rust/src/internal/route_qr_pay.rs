use crate::internal::utils::{build_backend, get_parent_app, Backend, PayTransaction};
use crate::prelude::load_env;
use base64::alphabet::STANDARD;
use base64::engine::{GeneralPurpose, GeneralPurposeConfig};
use base64::Engine;
use image::ImageFormat;
use std::collections::HashMap;
use std::fs;
use std::path::Path;

pub async fn qr_pay() {
    load_env();
    let url = build_backend(Backend::QrPay);
    println!("url = {url}");
    let client = reqwest::Client::new();
    let body = HashMap::from([
        (
            "recipient",
            serde_json::json!("BzRESJ9QW6EUprMFpLv2RYhZqEE6SUU7TwCroJR8b5Hk"),
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
    let resp_body = match response.json::<PayTransaction>().await {
        Ok(val) => val,
        Err(e) => {
            eprintln!("Parsing response body failed due to error {e:?}");
            return;
        }
    };
    let qr_code = &resp_body.qr_code as &str;
    let encoder = GeneralPurpose::new(&STANDARD, GeneralPurposeConfig::new());
    let bytes = match encoder.decode(qr_code) {
        Ok(val) => val,
        Err(e) => {
            eprintln!("Could not decode QR code due to error {e}");
            return;
        }
    };
    let img = match image::load_from_memory(&bytes) {
        Ok(val) => val,
        Err(e) => {
            eprintln!("Failed to convert decoded bytes to image due to error: {e}");
            return;
        }
    };
    let parent_app = get_parent_app();
    let img_path = parent_app.join("../../../../assets/pay.png");
    match fs::create_dir(img_path.parent().unwrap()) {
        Ok(_) => (),
        Err(e) => {
            if !img_path.parent().unwrap().exists() {
                eprintln!(
                    "Failed to create immediate parent dir of path: {} due to error {e}",
                    img_path.display()
                );
                return;
            }
        }
    };
    match img.save_with_format(&img_path as &Path, ImageFormat::Png) {
        Ok(_) => (),
        Err(e) => {
            eprintln!(
                "Failed to save image to path {} due to error {e}",
                img_path.display()
            );
            return;
        }
    };
}
