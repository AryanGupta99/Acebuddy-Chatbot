#!/usr/bin/env python3
"""
AceBuddy RAG Chatbot - OpenAI Cost Estimator

Calculates inference and fine-tuning costs based on:
- Model selection (gpt-4.1-mini, gpt-4o-mini, etc.)
- Expected query volume
- Context sizes (chunks retrieved)
- Fine-tuning dataset size
"""

import json
import sys
from pathlib import Path

# OpenAI Pricing (Nov 2025 - Standard Tier)
PRICING = {
    "gpt-4.1-mini": {
        "input": 0.40,      # $ per 1M tokens
        "output": 1.60,     # $ per 1M tokens
        "fine_tune_train": 5.00,  # $ per 1M tokens
    },
    "gpt-4o-mini": {
        "input": 0.15,
        "output": 0.60,
        "fine_tune_train": 3.00,
    },
    "gpt-4.1": {
        "input": 2.00,
        "output": 8.00,
        "fine_tune_train": 25.00,
    },
    "gpt-4o": {
        "input": 2.50,
        "output": 10.00,
        "fine_tune_train": 25.00,
    },
    "gpt-3.5-turbo": {
        "input": 0.50,
        "output": 1.50,
        "fine_tune_train": 8.00,
    },
    "text-embedding-3-small": 0.02,  # $ per 1M tokens
}


def estimate_tokens(text: str) -> int:
    """Rough estimate of tokens in text (approx. 4 chars per token)"""
    return len(text) // 4


class CostEstimator:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        if model not in PRICING:
            raise ValueError(f"Unknown model: {model}. Available: {list(PRICING.keys())}")
        self.rates = PRICING[model]

    def inference_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for a single inference"""
        input_cost = (input_tokens / 1_000_000) * self.rates["input"]
        output_cost = (output_tokens / 1_000_000) * self.rates["output"]
        return input_cost + output_cost

    def monthly_cost(self, monthly_queries: int, avg_input_tokens: int = 1050, avg_output_tokens: int = 200) -> float:
        """Calculate monthly inference cost"""
        cost_per_query = self.inference_cost(avg_input_tokens, avg_output_tokens)
        return monthly_queries * cost_per_query

    def fine_tune_cost(self, training_tokens: int) -> float:
        """Calculate cost to fine-tune a model"""
        return (training_tokens / 1_000_000) * self.rates["fine_tune_train"]

    def embedding_cost(self, tokens_to_embed: int) -> float:
        """Calculate cost for embedding (one-time ingestion)"""
        return (tokens_to_embed / 1_000_000) * PRICING["text-embedding-3-small"]

    def roi_analysis(self, training_tokens: int, monthly_queries: int = 1000) -> dict:
        """Analyze ROI of fine-tuning"""
        ft_cost = self.fine_tune_cost(training_tokens)
        
        # Compare monthly costs: RAG vs Fine-Tuned
        # RAG: ~1050 tokens input (retrieval) + prompt
        # FT-only: ~100 tokens (direct query) -> 3-4x cheaper per query
        cost_per_query_rag = self.inference_cost(1050, 200)
        cost_per_query_ft = self.inference_cost(100, 200)  # Simplified; actual ~27% of RAG
        
        monthly_rag = monthly_queries * cost_per_query_rag
        monthly_ft = monthly_queries * cost_per_query_ft
        
        months_to_breakeven = ft_cost / (monthly_rag - monthly_ft) if monthly_rag > monthly_ft else 0.1
        
        return {
            "fine_tune_cost": round(ft_cost, 4),
            "cost_per_query_rag": round(cost_per_query_rag, 6),
            "cost_per_query_ft": round(cost_per_query_ft, 6),
            "monthly_rag": round(monthly_rag, 2),
            "monthly_ft": round(monthly_ft, 2),
            "months_to_breakeven": round(max(0, months_to_breakeven), 1),
            "recommended": "fine-tune" if months_to_breakeven < 12 else "rag-only"
        }


def main():
    print("=" * 70)
    print("AceBuddy RAG Chatbot - OpenAI Cost Estimator")
    print("=" * 70)
    print()

    # AceBuddy Dataset Summary
    print("📊 DATASET SUMMARY")
    print("-" * 70)
    print("KB Articles:         10 files")
    print("Q&A Pairs:           187 pairs")
    print("Ticket Data:         150+ examples")
    print("Total Tokens:        ~126,000 tokens")
    print()

    # Scenario 1: RAG Only
    print("\n🎯 SCENARIO 1: RAG WITHOUT FINE-TUNING")
    print("-" * 70)
    
    models = ["gpt-4o-mini", "gpt-4.1-mini", "gpt-4o", "gpt-4.1"]
    query_volumes = [500, 2000, 5000, 10000]
    
    for model in models:
        est = CostEstimator(model)
        print(f"\n📌 Model: {model}")
        print(f"{'Queries/Month':<20} {'Cost':<15} {'Annual':<15}")
        print("-" * 50)
        
        for volume in query_volumes:
            # RAG: 1050 input tokens (5 chunks × 200 + prompt), 200 output
            monthly = est.monthly_cost(volume, avg_input_tokens=1050, avg_output_tokens=200)
            annual = monthly * 12
            print(f"{volume:<20} ${monthly:>6.2f}        ${annual:>6.2f}")

    # Scenario 2: Fine-Tuning Analysis
    print("\n\n🔬 SCENARIO 2: FINE-TUNING ANALYSIS")
    print("-" * 70)
    print("Training on: 187 Q&A pairs (~28,000 tokens)")
    print()
    
    for model in ["gpt-4o-mini", "gpt-4.1-mini", "gpt-3.5-turbo"]:
        est = CostEstimator(model)
        roi = est.roi_analysis(training_tokens=28000, monthly_queries=2000)
        
        print(f"\n📌 Model: {model}")
        print(f"  Fine-tune cost:        ${roi['fine_tune_cost']:.4f}")
        print(f"  Cost/query (RAG):      ${roi['cost_per_query_rag']:.6f}")
        print(f"  Cost/query (FT-only):  ${roi['cost_per_query_ft']:.6f}")
        print(f"  Monthly RAG:           ${roi['monthly_rag']:.2f}")
        print(f"  Monthly FT-only:       ${roi['monthly_ft']:.2f}")
        print(f"  Breakeven (months):    {roi['months_to_breakeven']:.1f}")
        print(f"  ✅ Recommended:         {roi['recommended'].upper()}")

    # Scenario 3: Comprehensive Budget
    print("\n\n💰 SCENARIO 3: 6-MONTH BUDGET PROJECTIONS")
    print("-" * 70)
    
    scenarios = [
        ("Small (500 q/mo)", 500),
        ("Medium (2,000 q/mo)", 2000),
        ("Large (10,000 q/mo)", 10000),
        ("Enterprise (50,000 q/mo)", 50000),
    ]
    
    for label, volume in scenarios:
        est = CostEstimator("gpt-4o-mini")  # Recommended model
        
        # RAG cost
        rag_6mo = est.monthly_cost(volume) * 6
        
        # FT cost (one-time $0.09 + cheaper inference)
        roi = est.roi_analysis(training_tokens=28000, monthly_queries=volume)
        ft_6mo = roi['fine_tune_cost'] + (roi['monthly_ft'] * 6)
        
        print(f"\n{label}")
        print(f"  RAG-only (6 mo):       ${rag_6mo:>6.2f}")
        print(f"  Fine-tuned (6 mo):     ${ft_6mo:>6.2f}")
        print(f"  Recommendation:        {'Fine-Tune' if roi['recommended'] == 'fine-tune' else 'RAG-Only'}")

    # Scenario 4: Cost Breakdown
    print("\n\n📋 SCENARIO 4: DETAILED COST BREAKDOWN (gpt-4o-mini)")
    print("-" * 70)
    
    est = CostEstimator("gpt-4o-mini")
    
    print("\nOne-Time Costs:")
    print(f"  Ingestion (embeddings): ${est.embedding_cost(126000):.4f}")
    print(f"  Fine-tuning (optional): ${est.fine_tune_cost(28000):.2f}")
    
    print("\nPer-Query Costs:")
    rag_cost = est.inference_cost(1050, 200)
    direct_cost = est.inference_cost(100, 200)
    print(f"  RAG (1050 in, 200 out): ${rag_cost:.6f}")
    print(f"  Direct FT (100 in, 200 out): ${direct_cost:.6f}")
    print(f"  Savings (FT vs RAG):    {((1 - direct_cost/rag_cost) * 100):.0f}%")

    print("\n" + "=" * 70)
    print("✅ For detailed analysis, see COST_ANALYSIS.md")
    print("=" * 70)


if __name__ == "__main__":
    main()
