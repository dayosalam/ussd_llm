use axum::routing::post;
use src_rust::prelude::*;
use std::ops::Deref;
use std::sync::Arc;

#[tokio::main]
async fn main() {
    let state = Arc::clone(STATE.deref());
    let app = axum::Router::new()
        .route(QR_PAY.deref(), post(handle_qr_pay))
        .route(PAY.deref(), post(handle_post_pay))
        .route(DEV_PAY.deref(), post(handle_dev_pay))
        .with_state(state);
    println!("rust backend is running on port = {}", PORT_RUST.deref());
    let listener = tokio::net::TcpListener::bind(format!("0.0.0.0:{}", PORT_RUST.deref()))
        .await
        .unwrap();
    axum::serve(listener, app).await.unwrap();
}
