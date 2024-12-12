# Generated by Django 5.1.1 on 2024-12-10 22:22

from django.db import migrations


class Migration(migrations.Migration):
    
    # load document category, client can add to the list through the UI
    def load_document_category(apps, schema_editor):
        DocumentCategory = apps.get_model('administration', 'DocumentCategory')

        # list of dictionaries containing document types which should serve the purpose of diverse institutions 
        document_types = [
            {"name": "Lease Agreement"},
            {"name": "Vendor Contract"},
            {"name": "Employee Agreement"},
            {"name": "Non-Disclosure Agreement (NDA)"},
            {"name": "Purchase Order"},
            {"name": "Invoice"},
            {"name": "Receipt"},
            {"name": "Customer Purchase Agreement"},
            {"name": "Service Level Agreement (SLA)"},
            {"name": "Employment Contract"},
            {"name": "Resignation Letter"},
            {"name": "Performance Review"},
            {"name": "Annual Report"},
            {"name": "Audit Report"},
            {"name": "Tax Documents (e.g., W-2, 1099)"},
            {"name": "Memorandum of Understanding (MOU)"},
            {"name": "Employee Handbook"},
            {"name": "Health and Safety Compliance Documents"},
            {"name": "Travel Authorization Form"},
            {"name": "Expense Claim Form"},
            {"name": "Supplier Bill"},
            {"name": "Supplier Invoice"},
            {"name": "Sales Contract"},
            {"name": "Bank Statement"},
            {"name": "Credit Report"},
            {"name": "Insurance Policy"},
            {"name": "Intellectual Property (IP) Agreement"},
            {"name": "Property Lease Agreement"},
            {"name": "Loan Agreement"},
            {"name": "Confidentiality Agreement"},
            {"name": "Marketing Agreement"},
            {"name": "Vendor Payment Terms"},
            {"name": "Stock Option Agreement"},
            {"name": "Patent Application"},
            {"name": "Trademark Application"},
            {"name": "Consultancy Agreement"},
            {"name": "Joint Venture Agreement"},
            {"name": "Board Resolution"},
            {"name": "Corporate Bylaws"},
            {"name": "Shareholder Agreement"},
            {"name": "Company Incorporation Documents"},
            {"name": "Employee Benefits Enrollment Forms"},
            {"name": "Termination Agreement"},
            {"name": "Collective Bargaining Agreement"},
            {"name": "Training Materials"},
            {"name": "Internal Memo"},
            {"name": "Board Meeting Minutes"},
            {"name": "Confidential Report"},
            {"name": "Legal Brief"},
            {"name": "Investment Proposal"},
            {"name": "Project Proposal"},
            {"name": "Business Plan"},
            {"name": "Confidentiality Agreement (Contractor)"},
            {"name": "Asset Transfer Agreement"},
            {"name": "Partnership Agreement"},
            {"name": "Data Privacy Agreement"},
            {"name": "Supplier Agreement"},
            {"name": "Payment Receipt"},
            {"name": "Grant Proposal"},
            {"name": "Tender Documents"},
            {"name": "Supply Chain Agreement"},
            {"name": "Inventory Record"},
            {"name": "Employee Leave Application"},
            {"name": "Performance Improvement Plan (PIP)"}
        ]

        bulk_create_entries = [
            DocumentCategory(name=doc_type['name'])
            for doc_type in document_types
        ]
        DocumentCategory.objects.bulk_create(bulk_create_entries)

    dependencies = [
        ('administration', '0007_unique_constraint_added_to_document_name_for_business_document'),
    ]

    operations = [
        migrations.RunPython(load_document_category)
    ]
