//! Real host package installer and protocol, without wallet_open or live services.
#![cfg(unix)]
use std::path::{Path, PathBuf};
use std::time::Duration;

use mesh_llm_plugin::{LocalStream, PROTOCOL_VERSION, proto, read_envelope, write_envelope};
use mesh_llm_plugin_manager::install::install_plugin_archive;
use mesh_llm_plugin_manager::{PluginInstallOptions, PluginTarget};
use proto::envelope::Payload;
use tokio::process::{Child, Command};
use tokio::time::timeout;

fn install(root: &Path) -> PathBuf {
    let archive = root.join("lexe-wallet.tar.gz");
    let compressed = flate2::write::GzEncoder::new(
        std::fs::File::create(&archive).unwrap(),
        flate2::Compression::default(),
    );
    let mut tar = tar::Builder::new(compressed);
    tar.append_path_with_name(env!("CARGO_BIN_EXE_lexe-wallet"), "lexe-wallet/lexe-wallet")
        .unwrap();
    tar.append_path_with_name("plugin.toml", "lexe-wallet/plugin.toml")
        .unwrap();
    tar.into_inner().unwrap().finish().unwrap();
    let options = PluginInstallOptions {
        store_root: root.join("store"),
        install_root: root.join("installed"),
        catalog_url: "http://unused.invalid".into(),
        target: PluginTarget::current().unwrap(),
    };
    let outcome =
        install_plugin_archive("lexe-wallet", "0.1.0", &archive, &options, &mut |_| {}).unwrap();
    assert!(outcome.metadata.enabled);
    root.join("installed/lexe-wallet/lexe-wallet")
}

async fn exchange(stream: &mut LocalStream, id: u64, payload: Payload) -> Payload {
    write_envelope(
        stream,
        &proto::Envelope {
            protocol_version: PROTOCOL_VERSION,
            plugin_id: "lexe-wallet".into(),
            request_id: id,
            payload: Some(payload),
        },
    )
    .await
    .unwrap();
    let response = timeout(Duration::from_secs(10), read_envelope(stream))
        .await
        .unwrap()
        .unwrap();
    assert_eq!(response.request_id, id);
    response.payload.unwrap()
}

async fn launch(binary: &Path, root: &Path) -> (Child, LocalStream) {
    let socket = root.join("host.sock");
    let _ = std::fs::remove_file(&socket);
    let listener = tokio::net::UnixListener::bind(&socket).unwrap();
    let child = Command::new(binary)
        .env("HOME", root)
        .env("MESH_LLM_PLUGIN_NAME", "lexe-wallet")
        .env("MESH_LLM_PLUGIN_ENDPOINT", &socket)
        .env("MESH_LLM_PLUGIN_TRANSPORT", "unix")
        .kill_on_drop(true)
        .spawn()
        .unwrap();
    let (stream, _) = timeout(Duration::from_secs(10), listener.accept())
        .await
        .unwrap()
        .unwrap();
    (child, LocalStream::Unix(stream))
}

async fn verify_unopened(stream: &mut LocalStream) {
    let response = exchange(
        stream,
        1,
        Payload::InitializeRequest(proto::InitializeRequest {
            host_protocol_version: PROTOCOL_VERSION,
            host_version: "test".into(),
            host_info_json: "{}".into(),
            mesh_visibility: proto::MeshVisibility::Private.into(),
        }),
    )
    .await;
    let Payload::InitializeResponse(response) = response else {
        panic!("initialize failed")
    };
    assert_eq!(response.plugin_id, "lexe-wallet");
    assert!(response.capabilities.iter().any(|s| s == "wallet.v1"));
    let manifest = response.manifest.unwrap();
    assert!(
        manifest.operations.is_empty(),
        "wallet must not advertise MCP tools"
    );
    assert!(manifest.http_bindings.is_empty());
    let response = exchange(
        stream,
        2,
        Payload::InvokeServiceRequest(proto::InvokeServiceRequest {
            kind: 1,
            service_name: "wallet_balance".into(),
            input_json: "{}".into(),
        }),
    )
    .await;
    let Payload::InvokeServiceResponse(response) = response else {
        panic!("RPC failed")
    };
    assert!(response.is_error);
    let error: serde_json::Value = serde_json::from_str(&response.output_json).unwrap();
    assert_eq!(error["kind"], "not_open");
}

#[tokio::test]
async fn installed_process_handshakes_and_restarts_without_provisioning() {
    // Short socket path: Darwin limits sockaddr_un to 104 bytes.
    let root = tempfile::Builder::new()
        .prefix("lexe-")
        .tempdir_in("/tmp")
        .unwrap();
    let binary = install(root.path());
    let (mut child, mut stream) = launch(&binary, root.path()).await;
    verify_unopened(&mut stream).await;
    child.kill().await.unwrap();
    child.wait().await.unwrap();
    drop(stream);
    let (mut child, mut stream) = launch(&binary, root.path()).await;
    verify_unopened(&mut stream).await;
    let response = exchange(
        &mut stream,
        3,
        Payload::ShutdownRequest(proto::ShutdownRequest {
            reason: "test complete".into(),
        }),
    )
    .await;
    assert!(matches!(response, Payload::ShutdownResponse(_)));
    assert!(
        timeout(Duration::from_secs(10), child.wait())
            .await
            .unwrap()
            .unwrap()
            .success()
    );
    assert!(!root.path().join(".mesh-llm").exists());
    assert!(!root.path().join("payments").exists());
}
