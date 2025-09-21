#!/usr/bin/env python
"""Pytest configuration file."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Add any pytest configuration here if needed

import pytest

# Set environment variables for testing
os.environ['FLASK_ENV'] = 'testing'
os.environ['TESTING'] = '1'
os.environ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
os.environ['PYTEST_CURRENT_TEST'] = '1'

@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    from app import create_app, db
    
    flask_app = create_app('testing')
    
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create test runner."""
    return app.test_cli_runner()