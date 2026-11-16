# Minimal RAG server for testing pg_semantic_cache integration
# This is a simplified version to demonstrate the integration

FROM golang:1.26.10-alpine AS builder

WORKDIR /app

# Copy source files
COPY . .

# Initialize go modules and download dependencies
RUN go mod tidy && go mod download

# Build
RUN go build -o rag-server .

FROM alpine:latest

RUN apk --no-cache add ca-certificates postgresql-client

WORKDIR /root/

COPY --from=builder /app/rag-server .
COPY --from=builder /app/config.yaml .

EXPOSE 8080

CMD ["./rag-server"]
