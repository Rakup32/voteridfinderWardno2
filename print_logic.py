import streamlit as st

def generate_voter_card(row):
    """
    Generates a printable voter card using CSS print rules to avoid page reloads.
    """
    
    # 1. CSS for Printing (Hides everything except the card)
    print_css = """
    <style>
    @media print {
        /* Hide everything by default */
        body * {
            visibility: hidden;
        }
        /* Show only the voter card and its children */
        #printable-voter-card, #printable-voter-card * {
            visibility: visible;
        }
        /* Position the card at the very top-left for the printer */
        #printable-voter-card {
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
            margin: 0;
            padding: 0;
            border: none;
        }
    }
    
    /* On-screen Styling for the Card (UI Only) */
    .voter-card {
        border: 2px solid #c53030;
        padding: 20px;
        border-radius: 12px;
        background-color: #ffffff;
        font-family: 'Mukta', sans-serif;
        max-width: 500px;
        margin: 10px auto;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    .card-header {
        text-align: center;
        border-bottom: 2px solid #c53030;
        margin-bottom: 15px;
        padding-bottom: 10px;
    }
    .card-row { margin: 8px 0; font-size: 1.1rem; }
    .label { font-weight: bold; color: #4a5568; }
    </style>
    """

    # 2. HTML Structure with unique ID
    card_html = f"""
    <div id="printable-voter-card" class="voter-card">
        <div class="card-header">
            <h2 style="margin:0; color:#c53030;">मतदाता परिचय पत्र</h2>
            <small>Voter Identification Card</small>
        </div>
        <div class="card-row"><span class="label">मतदाता नं:</span> {row.get('मतदाता नं', '-')}</div>
        <div class="card-row"><span class="label">नाम:</span> {row.get('मतदाताको नाम', '-')}</div>
        <div class="card-row"><span class="label">उमेर:</span> {row.get('उमेर(वर्ष)', '-')}</div>
        <div class="card-row"><span class="label">लिङ्ग:</span> {row.get('लिङ्ग', '-')}</div>
        <div class="card-row"><span class="label">पिता/माता:</span> {row.get('पिता/माताको नाम', '-')}</div>
        <div class="card-row"><span class="label">पति/पत्नी:</span> {row.get('पति/पत्नीको नाम', '-')}</div>
    </div>
    """

    # 3. Combine CSS, HTML, and the JavaScript Trigger
    st.markdown(print_css, unsafe_allow_html=True)
    st.markdown(card_html, unsafe_allow_html=True)

    # 4. Print Button (Uses window.print() directly without reloading)
    st.components.v1.html(
        """
        <script>
        function printCard() {
            window.print();
        }
        </script>
        <button onclick="printCard()"
        style="background:#c53030; color:white; border:none;
        padding:12px 24px; border-radius:8px;
        font-weight:bold; width:100%; cursor:pointer;
        font-size:16px; transition: 0.3s;">
        🖨️ Print Card (प्रिन्ट गर्नुहोस्)
        </button>
        """,
        height=70
    )