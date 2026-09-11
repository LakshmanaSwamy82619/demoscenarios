const { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType } = require("docx");
const fs = require("fs");

const doc = new Document({
  sections: [{
    properties: {
      page: { size: { width: 12240, height: 15840 } } // US Letter
    },
    children: [
      new Paragraph({ text: "Master Services Agreement", heading: HeadingLevel.TITLE }),
      new Paragraph({ text: "Contract Reference: MSA-2026-0417", spacing: { after: 300 } }),

      new Paragraph({ text: "1. Parties", heading: HeadingLevel.HEADING_1 }),
      new Paragraph({
        children: [
          new TextRun("This Agreement is entered into between Northgate Analytics Inc. (\"Provider\") and the Client, "),
          new TextRun("represented by the individuals named below."),
        ],
        spacing: { after: 200 }
      }),
      new Paragraph({
        children: [
          new TextRun({ text: "Client Signatory: ", bold: true }),
          new TextRun("Marcus Ellery Whitfield"),
        ],
      }),
      new Paragraph({
        children: [
          new TextRun({ text: "Client Email: ", bold: true }),
          new TextRun("marcus.whitfield@clientcorp.com"),
        ],
      }),
      new Paragraph({
        children: [
          new TextRun({ text: "Provider Signatory: ", bold: true }),
          new TextRun("Renata Ocasio Silva"),
        ],
      }),
      new Paragraph({
        children: [
          new TextRun({ text: "Provider Email: ", bold: true }),
          new TextRun("renata.silva@northgateanalytics.com"),
        ],
        spacing: { after: 200 }
      }),

      new Paragraph({ text: "2. Billing Information", heading: HeadingLevel.HEADING_1 }),
      new Paragraph({
        children: [
          new TextRun({ text: "Client Billing Account Number: ", bold: true }),
          new TextRun("AC-88214-7743"),
        ],
      }),
      new Paragraph({
        children: [
          new TextRun({ text: "Authorized Billing Contact SSN (on file, tax reporting): ", bold: true }),
          new TextRun("512-04-8891"),
        ],
        spacing: { after: 200 }
      }),

      new Paragraph({
        children: [
          new TextRun({ text: "Note: ", bold: true }),
          new TextRun("if the primary tax ID above cannot be verified, use the backup identifier on file, 512048891, for the annual filing."),
        ],
        spacing: { after: 200 }
      }),

      new Paragraph({ text: "3. Term and Termination", heading: HeadingLevel.HEADING_1 }),
      new Paragraph({
        text: "This Agreement commences on the Effective Date and continues for an initial term of twenty-four (24) months, " +
          "renewing automatically for successive twelve (12) month periods unless either party provides ninety (90) days' " +
          "written notice of non-renewal.",
        spacing: { after: 200 }
      }),

      new Paragraph({ text: "4. Confidentiality", heading: HeadingLevel.HEADING_1 }),
      new Paragraph({
        text: "Each party agrees to protect the other's confidential information using at least the same degree of care " +
          "it uses for its own confidential information, and in no event less than a reasonable degree of care. This " +
          "obligation survives termination of the Agreement for a period of five (5) years.",
        spacing: { after: 200 }
      }),

      new Paragraph({ text: "5. Notices", heading: HeadingLevel.HEADING_1 }),
      new Paragraph({
        text: "All notices under this Agreement shall be sent to the signatories identified in Section 1, with a copy " +
          "to each party's legal department.",
        spacing: { after: 400 }
      }),

      new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [ new TextRun({ text: "— End of Agreement —", italics: true }) ]
      }),
    ]
  }]
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync("contract.docx", buf);
  console.log("wrote contract.docx");
});
