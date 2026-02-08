;; BitAgent Reputation System — Stacks/Clarity Smart Contract
;; Tracks agent payment history and reputation on-chain

;; Data maps
(define-map agent-reputation
  { agent-id: (string-ascii 64) }
  {
    score: uint,
    total-payments: uint,
    successful-payments: uint,
    total-sats-spent: uint,
    registered-at: uint,
    last-updated: uint
  }
)

(define-map agent-payment-log
  { agent-id: (string-ascii 64), payment-index: uint }
  {
    amount-sats: uint,
    endpoint: (string-ascii 128),
    timestamp: uint,
    success: bool
  }
)

(define-map agent-payment-count
  { agent-id: (string-ascii 64) }
  { count: uint }
)

;; Constants
(define-constant contract-owner tx-sender)
(define-constant err-not-found (err u404))
(define-constant err-unauthorized (err u401))
(define-constant initial-score u50)
(define-constant max-score u100)

;; Register a new agent
(define-public (register-agent (agent-id (string-ascii 64)))
  (begin
    (map-set agent-reputation
      { agent-id: agent-id }
      {
        score: initial-score,
        total-payments: u0,
        successful-payments: u0,
        total-sats-spent: u0,
        registered-at: block-height,
        last-updated: block-height
      }
    )
    (map-set agent-payment-count
      { agent-id: agent-id }
      { count: u0 }
    )
    (ok initial-score)
  )
)

;; Record a payment and update reputation
(define-public (record-payment
    (agent-id (string-ascii 64))
    (amount-sats uint)
    (endpoint (string-ascii 128))
    (success bool))
  (let (
    (current-rep (unwrap! (map-get? agent-reputation { agent-id: agent-id }) err-not-found))
    (current-count (default-to { count: u0 } (map-get? agent-payment-count { agent-id: agent-id })))
    (new-total (+ (get total-payments current-rep) u1))
    (new-successful (if success
      (+ (get successful-payments current-rep) u1)
      (get successful-payments current-rep)))
    (new-sats (+ (get total-sats-spent current-rep) amount-sats))
    (new-score (calculate-score new-successful new-total new-sats))
  )
    ;; Update reputation
    (map-set agent-reputation
      { agent-id: agent-id }
      {
        score: new-score,
        total-payments: new-total,
        successful-payments: new-successful,
        total-sats-spent: new-sats,
        registered-at: (get registered-at current-rep),
        last-updated: block-height
      }
    )
    ;; Log the payment
    (map-set agent-payment-log
      { agent-id: agent-id, payment-index: (get count current-count) }
      {
        amount-sats: amount-sats,
        endpoint: endpoint,
        timestamp: block-height,
        success: success
      }
    )
    ;; Increment payment count
    (map-set agent-payment-count
      { agent-id: agent-id }
      { count: (+ (get count current-count) u1) }
    )
    (ok new-score)
  )
)

;; Calculate reputation score (0-100)
;; Factors: success rate (40%), volume (30%), total spent (30%)
(define-private (calculate-score
    (successful uint)
    (total uint)
    (sats-spent uint))
  (let (
    ;; Success rate component (0-40)
    (success-rate (if (> total u0)
      (/ (* successful u40) total)
      u0))
    ;; Volume component (0-30), caps at 100 payments
    (volume-score (if (> total u100) u30 (/ (* total u30) u100)))
    ;; Spending component (0-30), caps at 10000 sats
    (spend-score (if (> sats-spent u10000) u30 (/ (* sats-spent u30) u10000)))
    (raw-score (+ success-rate (+ volume-score spend-score)))
  )
    (if (> raw-score max-score) max-score raw-score)
  )
)

;; Read-only functions
(define-read-only (get-reputation (agent-id (string-ascii 64)))
  (map-get? agent-reputation { agent-id: agent-id })
)

(define-read-only (get-score (agent-id (string-ascii 64)))
  (match (map-get? agent-reputation { agent-id: agent-id })
    rep (ok (get score rep))
    err-not-found
  )
)

(define-read-only (get-payment-count (agent-id (string-ascii 64)))
  (default-to { count: u0 } (map-get? agent-payment-count { agent-id: agent-id }))
)

(define-read-only (get-discount-tier (agent-id (string-ascii 64)))
  (match (map-get? agent-reputation { agent-id: agent-id })
    rep (let ((score (get score rep)))
      (if (> score u80) (ok u30)      ;; 30% discount
        (if (> score u60) (ok u20)    ;; 20% discount
          (if (> score u30) (ok u10)  ;; 10% discount
            (ok u0)))))               ;; No discount
    (ok u0)
  )
)
