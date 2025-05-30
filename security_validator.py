"""
Security validation module for the Telegram bot.
Checks for security issues and provides recommendations.
"""

import os
import re
import json
import logging

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class SecurityValidator:
    def __init__(self, project_dir):
        self.project_dir = project_dir
        self.issues = []
        self.recommendations = []
    
    def validate_all(self):
        """Run all security validation checks."""
        logger.info("Starting security validation...")
        
        self.check_token_exposure()
        self.check_admin_access_control()
        self.check_payment_security()
        self.check_user_data_protection()
        self.check_error_handling()
        
        return {
            "issues": self.issues,
            "recommendations": self.recommendations,
            "passed": len(self.issues) == 0
        }
    
    def check_token_exposure(self):
        """Check if bot token is exposed in code or version control."""
        logger.info("Checking for token exposure...")
        
        # Check if token is in config file
        config_file = os.path.join(self.project_dir, "config.py")
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                content = f.read()
                if re.search(r'BOT_TOKEN\s*=\s*["\'][0-9]+:[A-Za-z0-9_-]+["\']', content):
                    self.issues.append("Bot token is hardcoded in config.py")
                    self.recommendations.append(
                        "Move bot token to environment variables or a separate .env file "
                        "that is excluded from version control"
                    )
        
        # Check for .gitignore
        gitignore_file = os.path.join(self.project_dir, ".gitignore")
        if not os.path.exists(gitignore_file):
            self.recommendations.append(
                "Create a .gitignore file to exclude sensitive files like .env, "
                "config files with tokens, and database files"
            )
    
    def check_admin_access_control(self):
        """Check if admin access is properly restricted."""
        logger.info("Checking admin access control...")
        
        # Check main.py for admin access control
        main_file = os.path.join(self.project_dir, "main.py")
        if os.path.exists(main_file):
            with open(main_file, 'r') as f:
                content = f.read()
                
                # Check if admin commands verify user permissions
                if not re.search(r'(db\.is_admin|not db\.is_admin).+config\.ADMIN_USER_IDS', content):
                    self.issues.append("Admin access control may not be properly implemented")
                    self.recommendations.append(
                        "Ensure all admin commands verify user permissions using both "
                        "database admin status and the ADMIN_USER_IDS list"
                    )
    
    def check_payment_security(self):
        """Check payment handling security."""
        logger.info("Checking payment security...")
        
        # Check payment.py for secure handling
        payment_file = os.path.join(self.project_dir, "payment.py")
        if os.path.exists(payment_file):
            with open(payment_file, 'r') as f:
                content = f.read()
                
                # Check for pre-checkout validation
                if "handle_pre_checkout" not in content:
                    self.issues.append("Pre-checkout validation may be missing")
                    self.recommendations.append(
                        "Implement pre-checkout validation to verify payment details "
                        "before accepting payments"
                    )
                
                # Check for payment provider token security
                if "provider_token" in content and not re.search(r'provider_token\s*=\s*config\.PAYMENT_PROVIDER_TOKEN', content):
                    self.issues.append("Payment provider token may not be securely stored")
                    self.recommendations.append(
                        "Store payment provider token in config and load it from environment variables"
                    )
    
    def check_user_data_protection(self):
        """Check if user data is properly protected."""
        logger.info("Checking user data protection...")
        
        # Check database.py for data protection
        database_file = os.path.join(self.project_dir, "database.py")
        if os.path.exists(database_file):
            with open(database_file, 'r') as f:
                content = f.read()
                
                # Check if database file is protected
                if not re.search(r'os\.path\.exists.+database_file', content):
                    self.recommendations.append(
                        "Add file permission checks to ensure database file is not accessible to unauthorized users"
                    )
                
                # Check for data validation before storage
                if not re.search(r'validate|validation', content, re.IGNORECASE):
                    self.recommendations.append(
                        "Add data validation before storing user input in the database"
                    )
    
    def check_error_handling(self):
        """Check if error handling is properly implemented."""
        logger.info("Checking error handling...")
        
        # Check main.py for error handling
        main_file = os.path.join(self.project_dir, "main.py")
        if os.path.exists(main_file):
            with open(main_file, 'r') as f:
                content = f.read()
                
                # Check for error handler
                if "error_handler" not in content:
                    self.issues.append("Error handling may be missing")
                    self.recommendations.append(
                        "Implement a global error handler to catch and log exceptions"
                    )
                
                # Check for try-except blocks
                if content.count("try:") < 3:  # Arbitrary threshold
                    self.recommendations.append(
                        "Add more try-except blocks to handle potential errors in critical operations"
                    )

def main():
    """Run security validation and print results."""
    validator = SecurityValidator("/home/ubuntu/telegram_bot")
    results = validator.validate_all()
    
    print("\n=== SECURITY VALIDATION RESULTS ===\n")
    
    if results["issues"]:
        print("ISSUES FOUND:")
        for i, issue in enumerate(results["issues"], 1):
            print(f"{i}. {issue}")
        print()
    else:
        print("No security issues found!\n")
    
    if results["recommendations"]:
        print("RECOMMENDATIONS:")
        for i, rec in enumerate(results["recommendations"], 1):
            print(f"{i}. {rec}")
        print()
    
    print(f"OVERALL: {'PASSED' if results['passed'] else 'FAILED'}")
    
    # Write results to file
    with open("/home/ubuntu/telegram_bot/security_validation.json", "w") as f:
        json.dump(results, f, indent=4)
    
    logger.info(f"Security validation {'passed' if results['passed'] else 'failed'}")
    return results

if __name__ == "__main__":
    main()
