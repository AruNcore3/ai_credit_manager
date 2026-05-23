from setuptools import setup

setup(
    name='billbridge-ai-credit-sdk',
    version='1.0.4',
    description='Official Python SDK for the Billbridge AI Credit Billing API',
    packages=['ai_credit_sdk'],
    install_requires=['requests>=2.31.0'],
    python_requires='>=3.10',
)
