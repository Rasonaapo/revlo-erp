
def format_phone_number(phone_number):
        """Format the phone number to (XXX)-XXXX-XXX format."""
        if phone_number and len(phone_number) == 10:
            return f"({phone_number[:3]})-{phone_number[3:7]}-{phone_number[7:]}"
        return phone_number  # Return unformatted if not 10 digits
