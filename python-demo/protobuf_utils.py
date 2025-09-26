"""
Utility functions for working with protobuf messages.
"""
import base58
from google.protobuf.descriptor import FieldDescriptor


def print_protobuf_message(msg, indent=0, encoding="base58"):
    """
    Debug helper to dump any protobuf message in a readable format.
    
    Args:
        msg: The protobuf message to print
        indent: Current indentation level for nested structures
        encoding: Encoding for bytes fields ("base58" or "hex")
    """
    prefix = " " * indent
    for field in msg.DESCRIPTOR.fields:
        value = getattr(msg, field.name)
        if field.label == FieldDescriptor.LABEL_REPEATED:
            if not value:
                continue
            print(f"{prefix}{field.name} (repeated):")
            for idx, item in enumerate(value):
                if field.type == FieldDescriptor.TYPE_MESSAGE:
                    print(f"{prefix}  [{idx}]:")
                    print_protobuf_message(item, indent + 4, encoding)
                elif field.type == FieldDescriptor.TYPE_BYTES:
                    if encoding == "base58":
                        s = base58.b58encode(item).decode()
                    else:
                        s = item.hex()
                    print(f"{prefix}  [{idx}]: {s}")
                else:
                    print(f"{prefix}  [{idx}]: {item}")

        elif field.type == FieldDescriptor.TYPE_MESSAGE:
            if msg.HasField(field.name):
                print(f"{prefix}{field.name}:")
                print_protobuf_message(value, indent + 4, encoding)

        elif field.type == FieldDescriptor.TYPE_BYTES:
            s = base58.b58encode(value).decode() if encoding == "base58" else value.hex()
            print(f"{prefix}{field.name}: {s}")

        elif field.containing_oneof:
            if msg.WhichOneof(field.containing_oneof.name) == field.name:
                print(f"{prefix}{field.name} (oneof): {value}")

        else:
            print(f"{prefix}{field.name}: {value}")


def format_protobuf_message(msg, encoding="base58"):
    """
    Format a protobuf message as a string instead of printing it.
    
    Args:
        msg: The protobuf message to format
        encoding: Encoding for bytes fields ("base58" or "hex")
        
    Returns:
        Formatted string representation of the message
    """
    import io
    import sys
    
    # Capture print output
    old_stdout = sys.stdout
    sys.stdout = captured_output = io.StringIO()
    
    try:
        print_protobuf_message(msg, encoding=encoding)
        return captured_output.getvalue()
    finally:
        sys.stdout = old_stdout


def get_protobuf_field_value(msg, field_path):
    """
    Get a specific field value from a protobuf message using dot notation.
    
    Args:
        msg: The protobuf message
        field_path: Dot-separated field path (e.g., "header.block_height")
        
    Returns:
        The field value, or None if not found
    """
    fields = field_path.split('.')
    current_msg = msg
    
    for field_name in fields:
        if not hasattr(current_msg, field_name):
            return None
        
        value = getattr(current_msg, field_name)
        
        # If this is the last field, return the value
        if field_name == fields[-1]:
            return value
        
        # Otherwise, continue traversing
        if hasattr(value, 'DESCRIPTOR'):
            current_msg = value
        else:
            return None
    
    return None


def extract_bytes_fields(msg, encoding="base58"):
    """
    Extract all bytes fields from a protobuf message and return as a dictionary.
    
    Args:
        msg: The protobuf message
        encoding: Encoding for bytes fields ("base58" or "hex")
        
    Returns:
        Dictionary mapping field names to encoded byte values
    """
    bytes_fields = {}
    
    for field in msg.DESCRIPTOR.fields:
        if field.type == FieldDescriptor.TYPE_BYTES:
            value = getattr(msg, field.name)
            if field.label == FieldDescriptor.LABEL_REPEATED:
                if value:
                    encoded_values = []
                    for item in value:
                        if encoding == "base58":
                            encoded_values.append(base58.b58encode(item).decode())
                        else:
                            encoded_values.append(item.hex())
                    bytes_fields[field.name] = encoded_values
            else:
                if encoding == "base58":
                    bytes_fields[field.name] = base58.b58encode(value).decode()
                else:
                    bytes_fields[field.name] = value.hex()
    
    return bytes_fields
