// use client_rust::prelude::dev_pay;

use client_rust::prelude::qr_pay;

#[tokio::main]
async fn main() {
    qr_pay().await;
}
