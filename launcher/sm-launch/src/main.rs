use std::env;
use std::fs;
use std::io::{self, Write};
use std::path::{Path, PathBuf};
use std::process::{Command, ExitCode};

#[cfg(windows)]
mod win_util {
    use std::ffi::c_void;
    use std::ptr::null_mut;

    #[link(name = "kernel32")]
    extern "system" {
        fn GetConsoleProcessList(process_list: *mut u32, count: u32) -> u32;
    }

    #[link(name = "user32")]
    extern "system" {
        fn MessageBoxW(hwnd: *mut c_void, text: *const u16, caption: *const u16, utype: u32) -> i32;
    }

    const MB_OKCANCEL: u32 = 0x00000001;
    const MB_ICONQUESTION: u32 = 0x00000020;
    const IDOK: i32 = 1;

    /// Returns true if the current process is the sole process attached to its console window
    /// (typical for double-click launches from Windows Explorer where conhost was newly created).
    pub fn is_launched_from_explorer() -> bool {
        let mut pids = [0u32; 8];
        let count = unsafe { GetConsoleProcessList(pids.as_mut_ptr(), pids.len() as u32) };
        count <= 1
    }

    /// Shows a native Windows confirmation dialog box.
    /// Returns true if user clicked OK, false if cancelled.
    pub fn prompt_execution_confirmation(file_name: &str, zone_untrusted: bool) -> bool {
        let warning_suffix = if zone_untrusted {
            "\n\n[WARNING]: This file was downloaded from the Internet or another computer (Zone.Identifier detected)."
        } else {
            ""
        };
        let prompt_text = format!(
            "Execute Semantic Program?\n\nFile: {file_name}{warning_suffix}\n\nDo you want to proceed with compilation and execution?"
        );
        let caption = "Semantic Program Launcher";

        let text_utf16: Vec<u16> = prompt_text.encode_utf16().chain(std::iter::once(0)).collect();
        let caption_utf16: Vec<u16> = caption.encode_utf16().chain(std::iter::once(0)).collect();

        let result = unsafe {
            MessageBoxW(
                null_mut(),
                text_utf16.as_ptr(),
                caption_utf16.as_ptr(),
                MB_OKCANCEL | MB_ICONQUESTION,
            )
        };
        result == IDOK
    }
}

#[cfg(not(windows))]
mod win_util {
    pub fn is_launched_from_explorer() -> bool {
        false
    }
    pub fn prompt_execution_confirmation(_file_name: &str, _zone_untrusted: bool) -> bool {
        true
    }
}

fn check_zone_identifier(path: &Path) -> bool {
    #[cfg(windows)]
    {
        // Check for Alternate Data Stream (file:Zone.Identifier)
        let mut ads_path = path.as_os_str().to_os_string();
        ads_path.push(":Zone.Identifier");
        if let Ok(content) = fs::read_to_string(&ads_path) {
            // ZoneId >= 3 indicates Internet or Restricted Sites
            for line in content.lines() {
                let trimmed = line.trim();
                if trimmed.starts_with("ZoneId=") {
                    if let Some(id_str) = trimmed.strip_prefix("ZoneId=") {
                        if let Ok(id) = id_str.parse::<u32>() {
                            if id >= 3 {
                                return true;
                            }
                        }
                    }
                }
            }
        }
    }
    false
}

fn resolve_installed_smc() -> Result<PathBuf, String> {
    let current_exe = env::current_exe()
        .map_err(|e| format!("Failed to determine launcher executable path: {e}"))?;
    let bin_dir = current_exe
        .parent()
        .ok_or_else(|| "Launcher executable has no parent directory".to_string())?;

    let smc_name = if cfg!(windows) { "smc.exe" } else { "smc" };
    let candidate = bin_dir.join(smc_name);

    if candidate.is_file() {
        Ok(candidate)
    } else {
        Err(format!(
            "Installed Semantic compiler ('{}') not found in launcher directory ('{}'). Never resolving from ambient PATH.",
            smc_name,
            bin_dir.display()
        ))
    }
}

fn validate_source_argument(args: &[String]) -> Result<PathBuf, String> {
    if args.len() < 2 {
        return Err("Usage: sm-launch <source_file.sm>".to_string());
    }
    if args.len() > 2 {
        return Err("Error: sm-launch accepts exactly one source file path in this version.".to_string());
    }

    let raw_path = &args[1];
    let path = Path::new(raw_path);

    if !path.exists() {
        return Err(format!("Source file does not exist: {}", path.display()));
    }

    if path.is_dir() {
        return Err(format!("Path is a directory, not a Semantic file: {}", path.display()));
    }

    let ext = path.extension().and_then(|s| s.to_str()).unwrap_or("");
    if ext != "sm" {
        return Err(format!(
            "Unsupported file extension '.{}'. sm-launch only runs '.sm' source files.",
            ext
        ));
    }

    // Canonicalize to resolve long paths, symlinks, and absolute path
    let canonical = path
        .canonicalize()
        .map_err(|e| format!("Failed to canonicalize path {}: {e}", path.display()))?;

    Ok(canonical)
}

fn run_launcher() -> Result<i32, String> {
    let args: Vec<String> = env::args().collect();
    let source_path = validate_source_argument(&args)?;

    let is_noninteractive = env::var("SEMANTIC_LAUNCH_NONINTERACTIVE").map(|v| v == "1").unwrap_or(false);
    let is_explorer = !is_noninteractive && win_util::is_launched_from_explorer();
    let is_zone_untrusted = !is_noninteractive && check_zone_identifier(&source_path);

    if is_explorer || is_zone_untrusted {
        let file_name = source_path
            .file_name()
            .map(|f| f.to_string_lossy().into_owned())
            .unwrap_or_else(|| "program.sm".to_string());

        let confirmed = win_util::prompt_execution_confirmation(&file_name, is_zone_untrusted);
        if !confirmed {
            return Err("Execution cancelled by user.".to_string());
        }
    }

    let smc_path = resolve_installed_smc()?;

    let working_dir = source_path
        .parent()
        .unwrap_or_else(|| Path::new("."));

    // Invoke installed smc with: smc run <source_path>
    let mut command = Command::new(&smc_path);
    command.arg("run");
    command.arg(&source_path);
    command.current_dir(working_dir);

    let status = command
        .status()
        .map_err(|e| format!("Failed to spawn Semantic compiler ('{}'): {e}", smc_path.display()))?;

    let exit_code = status.code().unwrap_or(1);

    if is_explorer {
        println!();
        println!("--------------------------------------------------");
        println!("Semantic execution finished with exit code {exit_code}.");
        print!("Press Enter to close this window...");
        let _ = io::stdout().flush();
        let mut line = String::new();
        let _ = io::stdin().read_line(&mut line);
    }

    Ok(exit_code)
}

fn main() -> ExitCode {
    match run_launcher() {
        Ok(code) => {
            if code == 0 {
                ExitCode::SUCCESS
            } else {
                ExitCode::from((code as u8).max(1))
            }
        }
        Err(err) => {
            eprintln!("[sm-launch:error] {err}");
            if win_util::is_launched_from_explorer() {
                println!();
                print!("Press Enter to exit...");
                let _ = io::stdout().flush();
                let mut line = String::new();
                let _ = io::stdin().read_line(&mut line);
            }
            ExitCode::from(1)
        }
    }
}
