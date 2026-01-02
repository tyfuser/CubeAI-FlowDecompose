"""
JSON Schema validation utilities for the Video Shooting Assistant.

Provides schema validation for metadata output and other structured data.
"""
import json
from pathlib import Path
from typing import Any, Optional

from jsonschema import Draft7Validator, ValidationError, validate
from jsonschema.exceptions import SchemaError


# Path to schema files
SCHEMA_DIR = Path(__file__).parent


class SchemaValidationError(Exception):
    """Custom exception for schema validation errors."""
    
    def __init__(self, message: str, errors: list[str]):
        super().__init__(message)
        self.errors = errors


class SchemaValidator:
    """
    JSON Schema validator for metadata and other structured outputs.
    
    Validates data against predefined JSON schemas and provides
    detailed error messages for validation failures.
    """
    
    def __init__(self):
        """Initialize the schema validator with loaded schemas."""
        self._schemas: dict[str, dict] = {}
        self._validators: dict[str, Draft7Validator] = {}
        self._load_schemas()
    
    def _load_schemas(self) -> None:
        """Load all JSON schema files from the schemas directory."""
        schema_files = {
            "metadata": "metadata_schema.json",
        }
        
        for name, filename in schema_files.items():
            schema_path = SCHEMA_DIR / filename
            if schema_path.exists():
                with open(schema_path, "r", encoding="utf-8") as f:
                    schema = json.load(f)
                    self._schemas[name] = schema
                    self._validators[name] = Draft7Validator(schema)
    
    def get_schema(self, schema_name: str) -> Optional[dict]:
        """
        Get a schema by name.
        
        Args:
            schema_name: Name of the schema (e.g., "metadata")
            
        Returns:
            The schema dictionary or None if not found
        """
        return self._schemas.get(schema_name)
    
    def validate(
        self,
        data: dict[str, Any],
        schema_name: str = "metadata"
    ) -> tuple[bool, list[str]]:
        """
        Validate data against a named schema.
        
        Args:
            data: The data to validate
            schema_name: Name of the schema to validate against
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        if schema_name not in self._validators:
            return False, [f"Unknown schema: {schema_name}"]
        
        validator = self._validators[schema_name]
        errors = []
        
        for error in validator.iter_errors(data):
            # Build a human-readable error message
            path = ".".join(str(p) for p in error.absolute_path) if error.absolute_path else "root"
            errors.append(f"{path}: {error.message}")
        
        return len(errors) == 0, errors
    
    def validate_metadata(self, data: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate metadata output against the metadata schema.
        
        Args:
            data: The metadata dictionary to validate
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        return self.validate(data, "metadata")
    
    def validate_or_raise(
        self,
        data: dict[str, Any],
        schema_name: str = "metadata"
    ) -> None:
        """
        Validate data and raise an exception if invalid.
        
        Args:
            data: The data to validate
            schema_name: Name of the schema to validate against
            
        Raises:
            SchemaValidationError: If validation fails
        """
        is_valid, errors = self.validate(data, schema_name)
        if not is_valid:
            raise SchemaValidationError(
                f"Schema validation failed for {schema_name}",
                errors
            )
    
    def validate_time_range(
        self,
        time_range: list[float],
        video_duration: Optional[float] = None
    ) -> tuple[bool, list[str]]:
        """
        Validate a time range.
        
        Args:
            time_range: [start, end] time range in seconds
            video_duration: Optional video duration for upper bound check
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        if len(time_range) != 2:
            errors.append("time_range must have exactly 2 elements [start, end]")
            return False, errors
        
        start, end = time_range
        
        if start < 0:
            errors.append(f"time_range start ({start}) must be >= 0")
        
        if start >= end:
            errors.append(f"time_range start ({start}) must be < end ({end})")
        
        if video_duration is not None and end > video_duration:
            errors.append(
                f"time_range end ({end}) must be <= video_duration ({video_duration})"
            )
        
        return len(errors) == 0, errors
    
    def validate_bbox(self, bbox: list[float]) -> tuple[bool, list[str]]:
        """
        Validate a normalized bounding box.
        
        Args:
            bbox: [x, y, w, h] bounding box coordinates
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        if len(bbox) != 4:
            errors.append("bbox must have exactly 4 elements [x, y, w, h]")
            return False, errors
        
        x, y, w, h = bbox
        
        for name, value in [("x", x), ("y", y), ("w", w), ("h", h)]:
            if not (0 <= value <= 1):
                errors.append(f"bbox.{name} ({value}) must be in range [0, 1]")
        
        if x + w > 1:
            errors.append(f"bbox x + w ({x + w}) must be <= 1")
        
        if y + h > 1:
            errors.append(f"bbox y + h ({y + h}) must be <= 1")
        
        return len(errors) == 0, errors


def validate_metadata_output(data: dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Convenience function to validate metadata output.
    
    Args:
        data: The metadata dictionary to validate
        
    Returns:
        Tuple of (is_valid, list of error messages)
    """
    validator = SchemaValidator()
    return validator.validate_metadata(data)


def load_metadata_schema() -> dict:
    """
    Load and return the metadata JSON schema.
    
    Returns:
        The metadata schema dictionary
    """
    schema_path = SCHEMA_DIR / "metadata_schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)
