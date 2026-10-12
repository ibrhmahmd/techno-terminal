"""Streamlit demo styling: severity colours and icons, category icons, shared CSS."""

# Severity definitions
SEVERITY_COLOR = {
    "ERROR":   "#FF4B4B",
    "WARNING": "#FFA500",
    "INFO":    "#4B9EFF",
}

SEVERITY_ICON = {
    "ERROR":   "🔴",
    "WARNING": "🟡",
    "INFO":    "🔵",
}

FINANCE_CATEGORY_ICONS = {
    "Revenue & Collection": "💰",
    "Payroll & Cost": "👷",
    "Discounts & Risk": "⚠️",
    "Group Health": "🏫",
}

# Shared styling
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Font Settings */
    .stApp, [data-testid="stAppViewContainer"], .main {
        font-family: 'Inter', sans-serif !important;
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 500 !important;
        letter-spacing: -0.03em !important;
    }
    
    /* Metric Cards (Design Constitution spec) */
    .metric-card {
        background: #ffffff;
        border: none;
        border-left: 4px solid var(--accent-color, #006a61);
        padding: 16px 20px;
        border-radius: 6px;
        box-shadow: 0 12px 40px rgba(11, 28, 48, 0.06);
        margin-bottom: 16px;
        transition: transform 120ms cubic-bezier(0.2, 0, 0, 1);
    }
    
    .metric-card:hover {
        transform: translateY(-1px);
    }
    
    .metric-title {
        font-size: 0.72rem;
        color: #4b5563;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 600;
        margin-bottom: 4px;
    }
    
    .metric-value {
        font-size: 1.85rem;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
        line-height: 1.1;
        color: #0c111d;
    }
    
    /* Tonal Layering (No Borders) */
    .tip-box {
        background: #eff4ff;
        border: none;
        border-radius: 6px;
        padding: 12px 16px;
        font-size: 0.85rem;
        color: #1f2538;
        margin-bottom: 16px;
        line-height: 1.4;
    }
</style>
"""
