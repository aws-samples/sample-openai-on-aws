package portlock

import (
	"net"
	"testing"
	"time"
)

func TestTryAcquire_Free(t *testing.T) {
	ln, err := TryAcquire(0) // port 0 = OS picks a free port
	if err != nil {
		t.Fatalf("TryAcquire: %v", err)
	}
	// port 0 isn't supported by TryAcquire (it binds to 127.0.0.1:0 which always succeeds)
	// so just verify we get a listener back and can close it
	if ln == nil {
		t.Fatal("expected non-nil listener for free port")
	}
	ln.Close()
}

func TestTryAcquire_Busy(t *testing.T) {
	// Bind a port ourselves to make it busy
	holder, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("setup: %v", err)
	}
	defer holder.Close()

	port := holder.Addr().(*net.TCPAddr).Port

	ln, err := TryAcquire(port)
	if err != nil {
		t.Fatalf("TryAcquire returned unexpected error: %v", err)
	}
	if ln != nil {
		ln.Close()
		t.Error("expected nil listener for busy port")
	}
}

func TestWaitForRelease_AlreadyFree(t *testing.T) {
	// Find a free port without holding it
	tmp, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	port := tmp.Addr().(*net.TCPAddr).Port
	tmp.Close()

	if !WaitForRelease(port, 2*time.Second) {
		t.Error("expected WaitForRelease=true for an already-free port")
	}
}

func TestWaitForRelease_Timeout(t *testing.T) {
	holder, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("setup: %v", err)
	}
	defer holder.Close()

	port := holder.Addr().(*net.TCPAddr).Port

	if WaitForRelease(port, 600*time.Millisecond) {
		t.Error("expected WaitForRelease=false while port is held")
	}
}

func TestWaitForRelease_ReleasedDuringWait(t *testing.T) {
	holder, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("setup: %v", err)
	}
	port := holder.Addr().(*net.TCPAddr).Port

	go func() {
		time.Sleep(400 * time.Millisecond)
		holder.Close()
	}()

	if !WaitForRelease(port, 3*time.Second) {
		t.Error("expected WaitForRelease=true after port released")
	}
}
