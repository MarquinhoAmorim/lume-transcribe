import AppKit
import Foundation

final class AppDelegate: NSObject, NSApplicationDelegate {
    private var server: Process?

    func applicationDidFinishLaunching(_ notification: Notification) {
        guard let resources = Bundle.main.resourceURL?.path else { NSApp.terminate(nil); return }
        let runner = "\(resources)/run-server.sh"
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/bin/zsh")
        process.arguments = ["-lc", "exec \"\(runner)\""]
        do {
            try process.run()
            server = process
        } catch {
            NSLog("Lume Transcribe: não foi possível iniciar o backend: \(error)")
            NSApp.terminate(nil)
        }
    }

    func applicationWillTerminate(_ notification: Notification) {
        server?.terminate()
    }
}

let application = NSApplication.shared
let delegate = AppDelegate()
application.delegate = delegate
application.run()
