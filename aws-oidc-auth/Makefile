VERSION ?= $(shell git describe --tags --always --dirty 2>/dev/null || echo "dev")
LDFLAGS := -s -w -X aws-oidc-auth/internal/version.Version=$(VERSION)
OUT ?= bin

.PHONY: all test coverage clean fmt vet macos-arm64 macos-intel linux-x64 linux-arm64 windows

all: macos-arm64 macos-intel linux-x64 linux-arm64 windows

test:
	go test ./... -v

coverage:
	go test ./... -coverprofile=coverage.out -covermode=atomic
	go tool cover -func=coverage.out
	go tool cover -html=coverage.out -o coverage.html

fmt:
	go fmt ./...

vet:
	go vet ./...

clean:
	rm -rf $(OUT)

macos-arm64:
	@mkdir -p $(OUT)
	CGO_ENABLED=0 GOOS=darwin GOARCH=arm64 go build -ldflags "$(LDFLAGS)" -o $(OUT)/credential-process-macos-arm64 ./cmd/credential-process/

macos-intel:
	@mkdir -p $(OUT)
	CGO_ENABLED=0 GOOS=darwin GOARCH=amd64 go build -ldflags "$(LDFLAGS)" -o $(OUT)/credential-process-macos-intel ./cmd/credential-process/

linux-x64:
	@mkdir -p $(OUT)
	CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags "$(LDFLAGS)" -o $(OUT)/credential-process-linux-x64 ./cmd/credential-process/

linux-arm64:
	@mkdir -p $(OUT)
	CGO_ENABLED=0 GOOS=linux GOARCH=arm64 go build -ldflags "$(LDFLAGS)" -o $(OUT)/credential-process-linux-arm64 ./cmd/credential-process/

windows:
	@mkdir -p $(OUT)
	CGO_ENABLED=0 GOOS=windows GOARCH=amd64 go build -ldflags "$(LDFLAGS)" -o $(OUT)/credential-process-windows.exe ./cmd/credential-process/
