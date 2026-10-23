# Security Model — Semantic-Dist

Status: Normative Security Specification  
Applies to: Native Launchers & Package Installers

---

## 1. Threat Model for End-User Execution

When a user installs Semantic and double-clicks a `.sm` file or runs `sm-launch`:

1. **Threat 1: Untrusted Remote Code Execution**
   - *Attack Vector*: A user downloads an arbitrary `.sm` file from the web containing malicious commands or infinite loops.
   - *Mitigation*: The native launcher checks the file's origin:
     - On Windows: Checks NTFS alternate data stream `Zone.Identifier` (Mark-of-the-Web).
     - On macOS: Checks extended attribute `com.apple.quarantine`.
     - On Linux: Checks user desktop environment flags.
     - If the file is marked remote/untrusted, display an interactive confirmation prompt:
       `[WARNING] This Semantic source file was downloaded from the internet. Are you sure you want to execute it? (y/N)`
2. **Threat 2: Unverified Bytecode Injection**
   - *Attack Vector*: Malicious or corrupted SemCode executes directly on the VM, attempting to exploit potential runtime edge cases.
   - *Mitigation*: The launcher enforces **Verifier-First Pipeline**:
     $$\text{Compile to Memory} \rightarrow \text{sm-verify Admission Gate} \rightarrow \text{Execute VM}$$
     If verification fails (e.g., code `E0005`, quota breach, or invalid string table), execution terminates immediately and displays the diagnostic error frame. Direct raw execution (`run-semcode-raw`) is strictly prohibited in user launchers.
3. **Threat 3: Silent Console Failure**
   - *Attack Vector*: When a GUI user double-clicks a script that crashes or reports an error, Windows/macOS immediately closes the console, hiding the diagnostic.
   - *Mitigation*: `sm-launch` allocates or attaches a console and guarantees a "Press any key to exit..." pause whenever execution completes or fails.
