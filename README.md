# SmartPick: Intelligent Product Recommendation System

SmartPick is an AI-powered e-commerce product comparison and recommendation system designed to help users make better purchasing decisions.
The system compares products from Amazon India and Flipkart using product price, ratings, review confidence, historical price trends, and buyer preferences. Instead of recommending products based only on price or star rating, SmartPick combines multiple factors to generate personalized product rankings.

## Table of Contents

1. [Introduction](#introduction)
2. [Key Features](#key-features)
3. [Technologies Used](#technologies-used)
4. [Installation](#installation)
5. [Usage](#usage)
6. [Project Structure](#project-structure)
7. [How SmartPick Works](#how-smartpick-works)
8. [Review Confidence Score](#review-confidence-score-rcs)
9. [Price Trend Indicator](#price-trend-indicator-pti)
10. [Persona-Adaptive Value Score](#persona-adaptive-value-score-pavs)
11. [Evaluation and Results](#evaluation-and-results)
12. [Docker Support](#docker-support)
13. [Contributors](#contributors)

## Introduction

Online shoppers often compare products using only price and average star ratings. These values alone may not provide enough information to make a reliable purchasing decision.
For example, a product with a 4.8-star rating from only a few reviews may appear better than a product with a 4.2-star rating supported by thousands of reviews.
SmartPick addresses these limitations through a three-layer recommendation pipeline:

- Review Confidence Score (RCS)
- Price Trend Indicator (PTI)
- Persona-Adaptive Value Score (PAVS)

The system combines these factors to provide more reliable and personalized product recommendations.

## Key Features

- Cross-platform product comparison
- Amazon India and Flipkart product analysis
- Real-time product information processing
- Review confidence scoring
- Historical price trend analysis
- Personalized product ranking
- Budget, Quality, and Balanced buyer personas
- Machine learning-based price trend analysis
- Web-based user interface
- Docker support
- Windows setup and execution scripts

## Technologies Used

SmartPick is primarily developed using:

- Python
- Flask
- HTML
- CSS
- JavaScript
- Machine Learning
- Linear Regression
- Web Scraping
- Statistical Analysis
- Docker

Python libraries and dependencies required by the application are available in:

`requirements.txt`

## Installation

### Windows

Clone the repository:

    git clone <your-smartpick-repository-url>

Navigate to the project directory:

    cd Smart-Pick

Run the Windows setup script:

    setup_windows.bat

The setup script prepares the required environment and dependencies for running SmartPick.

Alternatively, dependencies can be installed using:

    pip install -r requirements.txt

## Usage

After completing the installation, start SmartPick using:

    run_windows.bat

The application runs as a Flask-based web application.

Users can provide product information or product URLs and use SmartPick to compare available products and generate personalized recommendations.

## Project Structure

    Smart-Pick/
    |
    |-- data/
    |-- src/
    |-- static/
    |-- templates/
    |-- Dockerfile
    |-- requirements.txt
    |-- run_windows.bat
    |-- setup_windows.bat
    |-- README.md
    |-- .gitignore

### src

Contains the main Python application logic, recommendation algorithms, data processing, scraping, and evaluation components.

### templates

Contains HTML templates used by the Flask web application.

### static

Contains front-end resources such as CSS and JavaScript.

### data

Contains data used by the application, including product and evaluation-related information.

## How SmartPick Works

SmartPick uses a three-layer recommendation pipeline.

### Layer 1: Review Confidence

The system evaluates whether a product's rating is supported by a meaningful number of reviews.

### Layer 2: Price Trend Analysis

Historical pricing information is analyzed to determine whether the current product price is dropping, stable, or rising.

### Layer 3: Personalized Ranking

Product price, review confidence, quality, and price trends are combined according to the user's buyer persona.

The final result is a personalized product ranking rather than a simple price or rating sort.

## Review Confidence Score (RCS)

The Review Confidence Score improves the reliability of product ratings.

A high star rating supported by only a small number of reviews should not necessarily be considered more reliable than a slightly lower rating supported by thousands of reviews.

RCS applies a review-count-based correction to the raw product rating.

This allows SmartPick to reduce the influence of products whose ratings are based on limited review data.

## Price Trend Indicator (PTI)

The Price Trend Indicator analyzes historical product prices.

SmartPick uses approximately 30 days of real price history and applies linear regression to identify the direction of the price trend.

Products can be classified as:

- Dropping
- Stable
- Rising

A statistical significance check is also used to avoid assigning misleading trend labels when price movements are noisy.

This helps users understand whether the current price may represent a good buying opportunity.

## Persona-Adaptive Value Score (PAVS)

The Persona-Adaptive Value Score generates personalized product rankings.

SmartPick supports three buyer personas:

### Budget Buyer

Prioritizes price and overall value.

### Quality Buyer

Places greater importance on product quality and reliable customer ratings.

### Balanced Buyer

Balances price, quality, review confidence, and price trends.

PAVS combines these factors into a single score and ranks products according to the selected buyer persona.

## Evaluation and Results

SmartPick was evaluated using 21 live benchmark products across multiple product categories, including:

- Smartphones
- Laptops
- Earphones

The evaluation showed that persona-based ranking can improve recommendation quality compared with simple price-only and rating-only ranking methods.

The project evaluation reported improvements of up to:

- 15.5% over the price-only baseline for the Quality Buyer persona
- 58.6% over the rating-only baseline for the Budget Buyer persona

Real 30-day price history was successfully obtained for approximately 94.8% of the evaluated products.

## Docker Support

The repository includes a `Dockerfile` for containerized deployment.

Build the Docker image using:

    docker build -t smartpick .

Run the container using:

    docker run -p 5000:5000 smartpick



