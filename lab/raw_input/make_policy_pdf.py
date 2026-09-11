from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

doc = SimpleDocTemplate("policy.pdf", pagesize=letter,
                         topMargin=0.9*inch, bottomMargin=0.9*inch)
styles = getSampleStyleSheet()
h1 = ParagraphStyle('h1', parent=styles['Heading1'], spaceAfter=10)
h2 = ParagraphStyle('h2', parent=styles['Heading2'], spaceAfter=8)
body = ParagraphStyle('body', parent=styles['Normal'], spaceAfter=10, leading=15)

story = []
story.append(Paragraph("Remote Work & Data Handling Policy", h1))
story.append(Paragraph("Effective Date: 1 March 2026 &nbsp;&nbsp; Version: 3.2 &nbsp;&nbsp; Owner: Information Security Office", body))

story.append(Paragraph("1. Purpose", h2))
story.append(Paragraph(
    "This policy establishes the minimum requirements for employees and contractors who access company "
    "systems and customer data while working outside of a company facility. It applies to all business "
    "units and to any third party granted remote access under a signed data processing agreement.", body))

story.append(Paragraph("2. Scope", h2))
story.append(Paragraph(
    "The policy covers laptops, mobile devices, and personal devices enrolled in the mobile device "
    "management (MDM) program. It does not cover physical office access controls, which are addressed "
    "in the Facilities Security Standard.", body))

story.append(Paragraph("3. Data Classification Handling", h2))
story.append(Paragraph(
    "Restricted data, including personally identifiable information (PII) such as government identifiers, "
    "financial account numbers, and health information, must never be stored on local disk outside of the "
    "approved document management system. Restricted data in transit must be encrypted using TLS 1.2 or higher. "
    "Confidential data may be cached locally for a maximum of 24 hours and must be cleared automatically "
    "when the device is idle.", body))

story.append(Paragraph("4. Access Control", h2))
story.append(Paragraph(
    "Multi-factor authentication is required for all remote sessions. Session tokens expire after 12 hours "
    "of inactivity. Shared accounts are prohibited; each access event must be attributable to a single "
    "named individual for audit purposes.", body))

story.append(Paragraph("5. Incident Reporting", h2))
story.append(Paragraph(
    "Any suspected exposure of restricted data, including accidental transmission of an unmasked government "
    "identifier or account number, must be reported to the Information Security Office within 4 hours of "
    "discovery. Failure to report within this window is treated as a separate policy violation.", body))

story.append(Paragraph("6. Enforcement", h2))
story.append(Paragraph(
    "Violations of this policy may result in revocation of remote access privileges, disciplinary action, "
    "or termination of the applicable contract, consistent with the employee handbook and vendor agreements.", body))

doc.build(story)
print("wrote policy.pdf")
