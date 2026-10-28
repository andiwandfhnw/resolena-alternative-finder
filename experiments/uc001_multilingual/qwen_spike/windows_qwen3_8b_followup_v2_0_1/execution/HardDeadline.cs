using System;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Threading;

public sealed class ResolenaDeadline {
    readonly ManualResetEvent cancel = new ManualResetEvent(false);
    readonly Thread worker;
    public ResolenaDeadline(string root, int ownedId, long startTicks, string executable, int remainingMs, DateTime deadline) {
        worker = new Thread(delegate() {
            int utcMs = (int)Math.Max(0, Math.Min(remainingMs, (deadline.ToUniversalTime() - DateTime.UtcNow).TotalMilliseconds));
            if (cancel.WaitOne(utcMs)) return;
            string outcome = "deadline_expired";
            try {
                if (ownedId > 0) {
                    using (Process process = Process.GetProcessById(ownedId)) {
                        if (process.StartTime.ToUniversalTime().Ticks != startTicks ||
                            !String.Equals(process.MainModule.FileName, executable, StringComparison.OrdinalIgnoreCase)) {
                            outcome = "ownership_mismatch_no_process_stopped";
                        } else {
                            process.Kill();
                            process.WaitForExit(5000);
                            outcome = process.HasExited ? "deadline_expired_owned_server_stopped" : "deadline_expired_stop_unconfirmed";
                        }
                    }
                }
            } catch (ArgumentException) { outcome = "deadline_expired_server_already_ended"; }
            catch (Exception) { outcome = "deadline_expired_stop_unconfirmed"; }
            string path = Path.Combine(root, "hard_deadline.json");
            string body = "{\"utc\":\"" + DateTime.UtcNow.ToString("o") +
                "\",\"error\":\"" + outcome + "\",\"threshold_seconds\":1800,\"remaining_ms_at_arm\":" + remainingMs + "}";
            try { using (FileStream file = new FileStream(path, FileMode.CreateNew, FileAccess.Write, FileShare.Read)) {
                byte[] bytes = new UTF8Encoding(false).GetBytes(body); file.Write(bytes, 0, bytes.Length);
            }} catch (IOException) { }
        });
        worker.IsBackground = true;
        worker.Start();
    }
    public void Cancel() { cancel.Set(); worker.Join(1000); }
}
