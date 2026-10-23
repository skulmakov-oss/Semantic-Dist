use std::fs;
use std::process::Command;

#[test]
fn test_launcher_no_args_fails() {
    let output = Command::new(env!("CARGO_BIN_EXE_sm-launch"))
        .output()
        .expect("run launcher");
    assert!(!output.status.success());
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(stderr.contains("Usage: sm-launch"));
}

#[test]
fn test_launcher_missing_file_fails() {
    let output = Command::new(env!("CARGO_BIN_EXE_sm-launch"))
        .arg("nonexistent_test_file.sm")
        .output()
        .expect("run launcher");
    assert!(!output.status.success());
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(stderr.contains("Source file does not exist"));
}

#[test]
fn test_launcher_directory_arg_fails() {
    let temp_dir = tempfile::tempdir().expect("tempdir");
    let output = Command::new(env!("CARGO_BIN_EXE_sm-launch"))
        .arg(temp_dir.path())
        .output()
        .expect("run launcher");
    assert!(!output.status.success());
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(stderr.contains("Path is a directory"));
}

#[test]
fn test_launcher_wrong_extension_fails() {
    let temp_dir = tempfile::tempdir().expect("tempdir");
    let test_file = temp_dir.path().join("test.txt");
    fs::write(&test_file, "not a semantic file").expect("write test file");

    let output = Command::new(env!("CARGO_BIN_EXE_sm-launch"))
        .arg(&test_file)
        .output()
        .expect("run launcher");
    assert!(!output.status.success());
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(stderr.contains("Unsupported file extension"));
}

#[test]
fn test_launcher_missing_smc_in_install_dir_fails_cleanly() {
    let temp_dir = tempfile::tempdir().expect("tempdir");
    let valid_sm = temp_dir.path().join("hello.sm");
    fs::write(&valid_sm, "fn main() { return; }").expect("write hello.sm");

    // The test binary is run from target/debug, where smc.exe does NOT exist
    let output = Command::new(env!("CARGO_BIN_EXE_sm-launch"))
        .arg(&valid_sm)
        .output()
        .expect("run launcher");
    assert!(!output.status.success());
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(stderr.contains("Installed Semantic compiler") || stderr.contains("not found in launcher directory"));
}
