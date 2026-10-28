using System;
using System.Diagnostics;
using System.Reflection;
using System.Threading;

namespace Uc001Local {
    public sealed class DeadlineGuard : IDisposable {
        readonly object sync = new object();
        readonly MethodInfo closer;
        public readonly IntPtr Job;
        Timer timer;
        long deadline;
        bool armed, expired, closeAttempted, closed;
        public DeadlineGuard(IntPtr job, MethodInfo closeMethod) {
            if (job == IntPtr.Zero || closeMethod == null || !closeMethod.IsStatic ||
                closeMethod.ReturnType != typeof(bool) || closeMethod.GetParameters().Length != 1 ||
                closeMethod.GetParameters()[0].ParameterType != typeof(IntPtr)) throw new ArgumentException("Owned job/close method required");
            Job = job; closer = closeMethod;
        }
        public bool Expired { get { lock(sync) return expired; } }
        public void Arm(int milliseconds) {
            if (milliseconds <= 0 || milliseconds > 90000) throw new ArgumentOutOfRangeException("milliseconds");
            lock(sync) {
                if (armed || closeAttempted || expired) throw new InvalidOperationException("Owned deadline cannot be reused after failure");
                deadline = Stopwatch.GetTimestamp() + (long)Math.Ceiling(milliseconds * (double)Stopwatch.Frequency / 1000);
                armed = true;
                timer = new Timer(Tick, null, milliseconds, Timeout.Infinite);
            }
        }
        void StopTimer() { if (timer != null) { timer.Dispose(); timer = null; } }
        bool CloseOnce() {
            if (!closeAttempted) {
                closeAttempted = true;
                try { closed = (bool)closer.Invoke(null, new object[] { Job }); } catch { closed = false; }
            }
            return closed;
        }
        void Expire() { expired = true; armed = false; CloseOnce(); StopTimer(); }
        void Tick(object state) {
            lock(sync) {
                if (!armed) return;
                long remaining = deadline - Stopwatch.GetTimestamp();
                if (remaining > 0) timer.Change(Math.Max(1, (int)Math.Ceiling(remaining * 1000.0 / Stopwatch.Frequency)), Timeout.Infinite);
                else Expire();
            }
        }
        public void Disarm() {
            lock(sync) {
                if (!armed || expired || Stopwatch.GetTimestamp() >= deadline) {
                    if (armed) Expire();
                    throw new TimeoutException("Absolute supervised request deadline expired");
                }
                armed = false; StopTimer();
            }
        }
        public bool Close() { lock(sync) { armed = false; StopTimer(); return CloseOnce(); } }
        public void Dispose() { Close(); }
    }
}
