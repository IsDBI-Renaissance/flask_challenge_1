
# Set the matplotlib backend first (MUST come before other matplotlib imports)
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend

import matplotlib.pyplot as plt
import numpy as np
import arabic_reshaper
from bidi.algorithm import get_display
import base64
from io import BytesIO
from typing import Dict, List, Any

# Configure matplotlib for better Arabic support
plt.rcParams['font.family'] = 'Arial'
plt.rcParams['axes.unicode_minus'] = False


def create_journal_entries_chart(journal_entries: Dict, language: str = "english") -> str:
    """
    Create visualization of journal entries
    Args:
        journal_entries: Either:
            {
                "journal_entries": [
                    {"account": str, "debit": float, "credit": float},
                    ...
                ]
            }
            OR
            {
                "chart_data": {
                    "accounts": List[str],
                    "debits": List[float],
                    "credits": List[float]
                }
            }
        language: "english" or "arabic"
    Returns:
        Base64 encoded PNG image
    """
    try:
        # Handle both possible input formats
        if "journal_entries" in journal_entries:
            entries = journal_entries["journal_entries"]
            accounts = [entry["account"] for entry in entries]
            debits = [entry["debit"] for entry in entries]
            credits = [entry["credit"] for entry in entries]
        elif "chart_data" in journal_entries:
            chart_data = journal_entries["chart_data"]
            accounts = chart_data["accounts"]
            debits = chart_data["debits"]
            credits = chart_data["credits"]
        else:
            raise ValueError("Invalid journal entries format")
        
        # Check if we have any data to visualize
        if not accounts or not debits or not credits:
            raise ValueError("No data available for visualization")
            
        # Handle Arabic text
        if language.lower() == "arabic":
            accounts = [get_display(arabic_reshaper.reshape(account)) for account in accounts]
        
        # Rest of the function remains the same...
        fig, ax = plt.subplots(figsize=(12, 6))
        x = np.arange(len(accounts))
        width = 0.35
        
        debit_color = '#1f77b4'
        credit_color = '#ff7f0e'
        
        debit_bars = ax.bar(x - width/2, debits, width, label='Debit', color=debit_color)
        credit_bars = ax.bar(x + width/2, credits, width, label='Credit', color=credit_color)
        
        # Configure labels
        title = 'Journal Entries'
        ylabel = 'Amount'
        
        if language.lower() == "arabic":
            title = get_display(arabic_reshaper.reshape('القيود اليومية'))
            ylabel = get_display(arabic_reshaper.reshape('المبلغ'))
        
        ax.set_title(title, pad=20)
        ax.set_ylabel(ylabel)
        ax.set_xticks(x)
        ax.set_xticklabels(accounts, rotation=45, ha='right')
        ax.legend()
        
        ax.yaxis.set_major_formatter('{x:,.0f}')
        
        for bars in [debit_bars, credit_bars]:
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.annotate(f'{height:,.0f}',
                               xy=(bar.get_x() + bar.get_width() / 2, height),
                               xytext=(0, 3),
                               textcoords="offset points",
                               ha='center', va='bottom',
                               fontsize=8)
        
        plt.tight_layout()
        
        buffer = BytesIO()
        fig.savefig(buffer, format='png', dpi=120, bbox_inches='tight')
        plt.close(fig)
        return base64.b64encode(buffer.getvalue()).decode()
    
    except Exception as e:
        plt.close('all')
        raise RuntimeError(f"Failed to generate chart: {str(e)}")

def create_amortization_schedule_chart(amortization_data: Dict, language: str = "english") -> str:
    """
    Create amortization schedule visualization
    Args:
        amortization_data: {
            "rental_payments": List[float],
            "principal_repayments": List[float],
            "profit_portions": List[float],
            "remaining_balance": List[float]
        }
    Returns:
        Base64 encoded PNG image
    """
    try:
        periods = list(range(1, len(amortization_data['rental_payments']) + 1))
        
        # Create figure
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Payment breakdown chart
        width = 0.6
        bottom = np.zeros(len(periods))
        
        principal_color = '#2ca02c'  # Green
        profit_color = '#d62728'  # Red
        
        ax1.bar(periods, amortization_data['principal_repayments'], width, 
               label='Principal', color=principal_color, bottom=bottom)
        bottom += amortization_data['principal_repayments']
        
        ax1.bar(periods, amortization_data['profit_portions'], width,
               label='Profit', color=profit_color, bottom=bottom)
        
        # Configure titles
        title1 = 'Payment Breakdown'
        title2 = 'Remaining Balance'
        ylabel = 'Amount'
        
        if language.lower() == 'arabic':
            title1 = get_display(arabic_reshaper.reshape('تفصيل المدفوعات'))
            title2 = get_display(arabic_reshaper.reshape('الرصيد المتبقي'))
            ylabel = get_display(arabic_reshaper.reshape('المبلغ'))
        
        ax1.set_title(title1)
        ax1.set_ylabel(ylabel)
        ax1.legend()
        ax1.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Remaining balance chart
        ax2.plot(periods + [len(periods)+1], amortization_data['remaining_balance'], 
                marker='o', linestyle='-', color='#9467bd')
        ax2.set_title(title2)
        ax2.set_xlabel('Period')
        ax2.set_ylabel(ylabel)
        ax2.grid(True, linestyle='--', alpha=0.7)
        
        # Format both y-axes as currency
        for ax in [ax1, ax2]:
            ax.yaxis.set_major_formatter('{x:,.0f}')
        
        plt.tight_layout()
        
        # Save to buffer
        buffer = BytesIO()
        fig.savefig(buffer, format='png', dpi=120)
        plt.close(fig)
        return base64.b64encode(buffer.getvalue()).decode()
    
    except Exception as e:
        plt.close('all')
        raise RuntimeError(f"Failed to generate amortization chart: {str(e)}")

def create_comparison_chart(scenarios: List[Dict], metric: str, language: str = "english") -> str:
    """
    Create comparison chart for different scenarios
    Args:
        scenarios: [{"name": str, metric: float}, ...]
        metric: The metric being compared
    Returns:
        Base64 encoded PNG image
    """
    try:
        names = [s['name'] for s in scenarios]
        values = [s.get(metric, 0) for s in scenarios]
        
        # Handle Arabic text
        if language.lower() == "arabic":
            names = [get_display(arabic_reshaper.reshape(name)) for name in names]
            metric = get_display(arabic_reshaper.reshape(metric))
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Create horizontal bars
        y_pos = np.arange(len(names))
        colors = plt.cm.viridis(np.linspace(0, 1, len(names)))
        bars = ax.barh(y_pos, values, color=colors)
        
        # Configure labels
        title = f'Comparison of {metric.replace("_", " ").title()}'
        if language.lower() == 'arabic':
            title = get_display(arabic_reshaper.reshape(f'مقارنة {metric}'))
        
        ax.set_title(title)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(names)
        ax.xaxis.set_major_formatter('{x:,.0f}')
        ax.grid(axis='x', linestyle='--', alpha=0.6)
        
        # Add value labels
        for bar in bars:
            width = bar.get_width()
            ax.text(width * 1.02, bar.get_y() + bar.get_height()/2,
                   f'{width:,.0f}',
                   va='center')
        
        plt.tight_layout()
        
        # Save to buffer
        buffer = BytesIO()
        fig.savefig(buffer, format='png', dpi=120)
        plt.close(fig)
        return base64.b64encode(buffer.getvalue()).decode()
    
    except Exception as e:
        plt.close('all')
        raise RuntimeError(f"Failed to generate comparison chart: {str(e)}")