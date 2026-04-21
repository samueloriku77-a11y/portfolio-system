# Portfolio Core Systems

Welcome to the central repository for my core backend systems. This repository contains the source code for two distinct, fully-featured enterprise applications.

## 1. Document Forgery Detection System (`/police system`)

A complete technical solution for detecting physical and digital document forgery. This system leverages state-of-the-art machine learning models to analyze ID cards, passports, and official documents.

**Key Features:**
- **Advanced Machine Learning:** Uses MobileNetV2 for feature extraction and EfficientNetV2S for intelligent forgery probability classification.
- **Deep Similarity Analysis:** Implements Structural Similarity (SSIM), Euclidean, and Cosine similarity metrics to compare uploaded documents against verified database references.
- **Pre-processing Engine:** Fully automated image denoising (Non-local means) and contrast enhancement (CLAHE).
- **Admin Dashboard:** Review documents, access similarity heatmaps, identify suspicious regions, and maintain an audit log.

👉 [View full documentation in the Police System README](./police%20system/README.md)

---

## 2. SokoYetu Hyperlocal Delivery Platform (`/sokoyetu`)

A comprehensive full-stack delivery platform designed for high-trust, fast-paced local environments, providing robust protection against fraud and delivery disputes.

**Key Features:**
- **Escrow Payment Management:** Integrates with M-Pesa STK Push. Funds are held in a secure ledger until verified delivery.
- **Triple-Verified Delivery (Anti-Fraud):** 
  - *GPS Geofencing*: Delivery cannot be marked complete unless the driver is within 15 meters.
  - *Double-Blind Handshake*: Requires matching the vendor's digital signature with the customer's dynamic QR code.
  - *No-Show Protection*: Drivers must upload GPS-stamped photo evidence to dispute incomplete deliveries.
- **Role-Based Architecture:** Dedicated dashboards and APIs for Customers, Vendors, and Drivers (featuring student ID validations and university tracking).
- **Real-Time Logistics:** WebSocket-powered driver tracking and automated email/SMS/WhatsApp receipts.

👉 [View full documentation in the SokoYetu README](./sokoyetu/README.md)

---

> **Note:** The frontend portfolio implementation is maintained separately and not documented here. The purpose of this repository is to showcase the backend architectures, models, and comprehensive systems logic.
