VERSION ?= $(shell git describe --tags --always --dirty 2>/dev/null || echo "dev")
LDFLAGS := -s -w -X otel-helper/internal/version.Version=$(VERSION)
OUT ?= bin

.PHONY: all test clean fmt vet macos-arm64 macos-intel linux-x64 linux-arm64 windows

all: macos-arm64 macos-intel linux-x64 linux-arm64 windows

test:
	go test ./... -v

fmt:
	go fmt ./...

vet:
	go vet ./...

clean:
	rm -rf $(OUT)

macos-arm64:
	@mkdir -p $(OUT)
	CGO_ENABLED=0 GOOS=darwin GOARCH=arm64 go build -ldflags "$(LDFLAGS)" -o $(OUT)/otel-helper-macos-arm64 .

macos-intel:
	@mkdir -p $(OUT)
	CGO_ENABLED=0 GOOS=darwin GOARCH=amd64 go build -ldflags "$(LDFLAGS)" -o $(OUT)/otel-helper-macos-intel .

linux-x64:
	@mkdir -p $(OUT)
	CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags "$(LDFLAGS)" -o $(OUT)/otel-helper-linux-x64 .

linux-arm64:
	@mkdir -p $(OUT)
	CGO_ENABLED=0 GOOS=linux GOARCH=arm64 go build -ldflags "$(LDFLAGS)" -o $(OUT)/otel-helper-linux-arm64 .

windows:
	@mkdir -p $(OUT)
	CGO_ENABLED=0 GOOS=windows GOARCH=amd64 go build -ldflags "$(LDFLAGS)" -o $(OUT)/otel-helper-windows.exe .
