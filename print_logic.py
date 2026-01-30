import streamlit as st
import pandas as pd

def generate_printable_card(row):
    """
    Generates the HTML for a printable voter card.
    """
    # Safe handling of missing values (converts NaN to '-')
    def safe_get(key):
        val = row.get(key, '-')
        if pd.isna(val) or str(val).strip() == '':
            return '-'
        return str(val)

    voter_no = safe_get('मतदाता नं')
    serial_no = safe_get('सि.नं.')
    name = safe_get('मतदाताको नाम')
    parent = safe_get('पिता/माताको नाम')
    spouse = safe_get('पति/पत्नीको नाम')

    # HTML for the card
    card_html = f"""
    <div id="print-area" style="
        border: 2px solid #000;
        padding: 20px;
        width: 100%;
        max-width: 400px;
        margin: 0 auto;
        font-family: Arial, sans-serif;
        background-color: white;
        color: black;
    ">
        <div style="text-align: center; border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 10px;">
            <h3 style="margin: 0;">निर्वाचन आयोग, नेपाल</h3>
            <p style="margin: 5px 0 0 0; font-size: 14px;">मतदाता परिचय पत्र विवरण</p>
        </div>
        
        <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
            <tr>
                <td style="padding: 8px; font-weight: bold; width: 40%;">सि.नं. (S.N.):</td>
                <td style="padding: 8px;">{serial_no}</td>
            </tr>
            <tr>
                <td style="padding: 8px; font-weight: bold;">मतदाता नं (Voter ID):</td>
                <td style="padding: 8px;">{voter_no}</td>
            </tr>
            <tr>
                <td style="padding: 8px; font-weight: bold;">नाम (Name):</td>
                <td style="padding: 8px;">{name}</td>
            </tr>
            <tr>
                <td style="padding: 8px; font-weight: bold;">पिता/माता (Parent):</td>
                <td style="padding: 8px;">{parent}</td>
            </tr>
            <tr>
                <td style="padding: 8px; font-weight: bold;">पति/पत्नी (Spouse):</td>
                <td style="padding: 8px;">{spouse}</td>
            </tr>
        </table>

        <div style="margin-top: 20px; text-align: center; font-size: 12px; color: #555;">
            * यो विवरण कम्प्युटर प्रणालीबाट निकालिएको हो।
        </div>
    </div>
    """

    st.markdown(card_html, unsafe_allow_html=True)
    st.markdown("---")

    # JavaScript to Print ONLY the Card
    print_js = """
    <script>
    function printDiv() {
        var printContents = document.getElementById('print-area').innerHTML;
        var originalContents = document.body.innerHTML;
        document.body.innerHTML = printContents;
        window.print();
        document.body.innerHTML = originalContents;
        window.location.reload(); 
    }
    </script>
    """
    st.components.v1.html(print_js + "<button onclick='printDiv()' style='background-color:#c53030; color:white; border:none; padding:10px 20px; border-radius:5px; cursor:pointer; font-weight:bold; width:100%;'>🖨️ Print Card (प्रिन्ट गर्नुहोस्)</button>", height=60)

@st.dialog("मतदाता विवरण (Voter Details)")
def show_voter_popup(row_data):
    generate_printable_card(row_data)