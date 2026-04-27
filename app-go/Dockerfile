FROM golang:1.22-alpine AS builder

WORKDIR /app
COPY go.mod ./
COPY main.go ./

RUN go build -o /server .

FROM alpine:3.19

RUN apk --no-cache add ca-certificates
COPY --from=builder /server /server

EXPOSE 8080
CMD ["/server"]
