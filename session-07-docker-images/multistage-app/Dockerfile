# ---------- stage 1: build ----------
FROM golang:1.23-alpine AS builder
WORKDIR /src
COPY go.mod .
COPY main.go .
# static binary so it can run on a minimal image
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /out/server .

# ---------- stage 2: run ----------
FROM alpine:3.20
RUN adduser -D appuser
WORKDIR /app
COPY --from=builder /out/server .
USER appuser
EXPOSE 8080
CMD ["./server"]
