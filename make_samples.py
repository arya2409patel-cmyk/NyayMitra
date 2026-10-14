"""Generates FICTIONAL sample contracts as PDFs for testing/demo (no real parties).
Replace/add real public templates in data/contracts/ before the final demo."""
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

OUT = Path(__file__).parent / "data" / "contracts"
OUT.mkdir(parents=True, exist_ok=True)

DOCS = {
"rental_agreement_sample.pdf": ("RENT AGREEMENT (SAMPLE - FICTIONAL)", """This agreement is made between Mr Ramesh Patel (Landlord) and Mr Dev Shah (Tenant) for the premises at Flat 12, Sunrise Apartments, Mehsana.
1. Rent. The Tenant shall pay monthly rent of Rs. 12,000 on or before the 5th day of every month.
2. Term. This agreement is for a period of 11 months starting 1 November 2026.
3. Security Deposit. The Tenant has paid Rs. 50,000 as security deposit. The deposit shall be non-refundable if the Landlord finds any damage, as decided by the Landlord.
4. Termination. The Landlord may terminate this agreement at any time without notice. The Tenant must give 3 months notice to vacate.
5. Renewal. This agreement shall automatically renew for a further 11 months unless the Landlord decides otherwise.
6. Lock-in. The Tenant is under a lock-in period of 6 months and must pay full rent for the remaining period if he leaves early.
7. Changes. The Landlord reserves the right to modify the rent or any term at any time at his sole discretion."""),
"freelance_agreement_sample.pdf": ("FREELANCE SERVICES AGREEMENT (SAMPLE - FICTIONAL)", """This Services Agreement is between Bright Studio Pvt Ltd (Client) and Asha Mehta (Freelancer).
1. Services. The Freelancer shall design a website and deliver the deliverables listed in Schedule A.
2. Fees. The Client shall pay a total fee of Rs. 60,000 for the project.
3. Payment. Payment will be made after the Client is fully satisfied with the work, at the Client's sole discretion.
4. Term. This agreement is valid for a period of 3 months from 15 October 2026.
5. Intellectual Property. All intellectual property, work product and inventions of the Freelancer, whether created for this project or not, shall belong to the Client.
6. Non-compete. The Freelancer shall not work for any competitor or similar business for a period of 3 years after this agreement ends.
7. Indemnity. The Freelancer shall indemnify the Client against any and all losses, claims and damages.
8. Termination. The Client may terminate this agreement at any time without notice or reason. The Freelancer must give 60 days notice.
9. Penalty. For any delay the Freelancer shall pay a penalty of Rs. 2,000 per day."""),
"offer_letter_sample.pdf": ("OFFER OF EMPLOYMENT (SAMPLE - FICTIONAL)", """Dear Candidate, we are pleased to offer you the position of Junior Developer at Nova Tech Solutions (Employer).
1. Salary. Your salary will be Rs. 25,000 per month, payable on or before the 7th of each month.
2. Probation. You will be on probation for 6 months. During probation the Employer may terminate your employment at any time without notice.
3. Notice. After confirmation, either party may terminate this employment by giving 60 days notice.
4. Service Bond. You must sign a service bond of 2 years. If you leave earlier you shall pay Rs. 1,00,000 as penalty and the Employer will withhold your original certificates.
5. Non-compete. You shall not join any competitor for 2 years after leaving.
6. Governing Law. This letter is governed by the laws of India and the courts at Ahmedabad shall have jurisdiction.
7. Dispute Resolution. Any dispute shall be referred to arbitration by a sole arbitrator appointed by the Employer."""),
"nda_sample.pdf": ("MUTUAL NON-DISCLOSURE AGREEMENT (SAMPLE - FICTIONAL)", """This Non-Disclosure Agreement is between Alpha Labs (Disclosing Party) and Beta Works (Receiving Party).
1. Confidential Information. Confidential Information means all non-public business information shared between the parties.
2. Obligations. The Receiving Party shall keep the Confidential Information secret and use it only for evaluating a possible partnership.
3. Duration. The confidentiality obligations shall survive for a period of 3 years from the date of disclosure.
4. Term. This agreement is valid for a period of 12 months from 1 December 2026.
5. Termination. Either party may terminate this agreement by giving 30 days written notice.
6. Governing Law. This agreement is governed by the laws of India and the courts at Ahmedabad shall have jurisdiction.
7. Dispute Resolution. The parties shall first try mediation, failing which disputes shall be settled by arbitration in Ahmedabad."""),
}

ss = getSampleStyleSheet()
for name, (title, body) in DOCS.items():
    doc = SimpleDocTemplate(str(OUT / name), pagesize=A4)
    story = [Paragraph(title, ss["Title"]), Spacer(1, 12)]
    for line in body.split("\n"):
        story += [Paragraph(line, ss["BodyText"]), Spacer(1, 6)]
    doc.build(story)
    print("wrote", name)
