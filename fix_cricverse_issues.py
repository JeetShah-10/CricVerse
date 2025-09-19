#!/usr/bin/env python3
"""
CricVerse Issue Fix Script
Addresses common issues found in the system based on diagnostics and memories
"""

import os
import sys
import json
import shutil
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CricVerseFixer:
    """Comprehensive fix system for CricVerse issues"""
    
    def __init__(self):
        self.fixes_applied = []
        self.errors_encountered = []
        
        # Load environment
        self.load_environment()
    
    def load_environment(self):
        """Load environment variables"""
        try:
            if os.path.exists('cricverse.env'):
                load_dotenv('cricverse.env')
                logger.info("✅ Loaded cricverse.env")
            elif os.path.exists('.env'):
                load_dotenv('.env')
                logger.info("✅ Loaded .env")
            else:
                logger.warning("⚠️ No environment file found")
        except Exception as e:
            logger.error(f"❌ Failed to load environment: {e}")
    
    def fix_enhanced_models_metadata_column(self):
        """Fix the metadata column issue in enhanced_models.py"""
        logger.info("🔧 Fixing enhanced_models.py metadata column...")
        
        try:
            enhanced_models_path = Path('enhanced_models.py')
            
            if not enhanced_models_path.exists():
                logger.warning("enhanced_models.py not found, skipping fix")
                return True
            
            # Read current content
            with open(enhanced_models_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if file is empty
            if not content.strip():
                logger.info("enhanced_models.py is empty, recreating from models.py...")
                
                # Copy from models.py if it exists
                models_path = Path('models.py')
                if models_path.exists():
                    with open(models_path, 'r', encoding='utf-8') as f:
                        models_content = f.read()
                    
                    # Replace metadata with extra_data
                    fixed_content = models_content.replace('metadata', 'extra_data')
                    
                    with open(enhanced_models_path, 'w', encoding='utf-8') as f:
                        f.write(fixed_content)
                    
                    self.fixes_applied.append("Recreated enhanced_models.py from models.py with extra_data column")
                    logger.info("✅ Enhanced models recreated successfully")
                else:
                    logger.warning("models.py not found, cannot recreate enhanced_models.py")
                    return False
            else:
                # Fix metadata column references
                if 'metadata' in content and 'extra_data' not in content:
                    fixed_content = content.replace('metadata', 'extra_data')
                    
                    with open(enhanced_models_path, 'w', encoding='utf-8') as f:
                        f.write(fixed_content)
                    
                    self.fixes_applied.append("Fixed metadata column to extra_data in enhanced_models.py")
                    logger.info("✅ Fixed metadata column references")
                else:
                    logger.info("No metadata column issues found in enhanced_models.py")
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to fix enhanced_models.py: {e}"
            self.errors_encountered.append(error_msg)
            logger.error(f"❌ {error_msg}")
            return False
    
    def fix_chatbot_imports(self):
        """Fix chatbot.py imports to use app.py instead of models.py"""
        logger.info("🔧 Fixing chatbot.py imports...")
        
        try:
            chatbot_path = Path('chatbot.py')
            
            if not chatbot_path.exists():
                logger.warning("chatbot.py not found, skipping import fixes")
                return True
            
            # Read current content
            with open(chatbot_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Track changes made
            changes_made = False
            
            # Fix imports from models.py to app.py
            if 'from models import' in content:
                content = content.replace('from models import', 'from app.models import')
                changes_made = True
                logger.info("Fixed: from models import -> from app.models import")
            
            # Fix direct model imports
            model_imports = [
                'Customer', 'Event', 'Booking', 'Ticket', 'Stadium', 
                'Team', 'Seat', 'Concession', 'Parking'
            ]
            
            for model in model_imports:
                old_import = f'from models import {model}'
                new_import = f'from app.models import {model}'
                if old_import in content:
                    content = content.replace(old_import, new_import)
                    changes_made = True
                    logger.info(f"Fixed import for {model}")
            
            # Add fallback imports for enhanced_models
            if 'enhanced_models' in content and 'try:' not in content:
                enhanced_import_fix = """
try:
    from enhanced_models import *
except ImportError:
    logger.warning("Enhanced models not available, using fallback")
    pass
"""
                # Add at the beginning after other imports
                import_section_end = content.find('\n\n')
                if import_section_end != -1:
                    content = content[:import_section_end] + enhanced_import_fix + content[import_section_end:]
                    changes_made = True
                    logger.info("Added fallback import handling for enhanced_models")
            
            # Write changes if any were made
            if changes_made:
                with open(chatbot_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.fixes_applied.append("Fixed chatbot.py imports and added fallback handling")
                logger.info("✅ Chatbot imports fixed successfully")
            else:
                logger.info("No import issues found in chatbot.py")
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to fix chatbot imports: {e}"
            self.errors_encountered.append(error_msg)
            logger.error(f"❌ {error_msg}")
            return False
    
    def fix_realtime_indentation(self):
        """Fix indentation errors in realtime.py"""
        logger.info("🔧 Fixing realtime.py indentation...")
        
        try:
            realtime_path = Path('realtime.py')
            
            if not realtime_path.exists():
                logger.warning("realtime.py not found, skipping indentation fixes")
                return True
            
            # Read current content
            with open(realtime_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Fix common indentation issues
            fixed_lines = []
            in_function = False
            
            for line in lines:
                # Check for malformed function definitions
                if line.strip().startswith('def ') and not line.strip().endswith(':'):
                    if '(' in line and ')' not in line:
                        # Multi-line function definition
                        line = line.rstrip() + '):\n'
                        logger.info(f"Fixed malformed function definition: {line.strip()}")
                
                # Fix indentation for SocketIO event handlers
                if '@socketio.on(' in line:
                    in_function = True
                    if not line.startswith('    '):
                        line = '    ' + line.lstrip()
                
                if in_function and line.strip().startswith('def '):
                    if not line.startswith('    '):
                        line = '    ' + line.lstrip()
                
                if in_function and line.strip() == '':
                    in_function = False
                
                fixed_lines.append(line)
            
            # Write fixed content
            with open(realtime_path, 'w', encoding='utf-8') as f:
                f.writelines(fixed_lines)
            
            self.fixes_applied.append("Fixed indentation issues in realtime.py")
            logger.info("✅ Realtime.py indentation fixed")
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to fix realtime.py indentation: {e}"
            self.errors_encountered.append(error_msg)
            logger.error(f"❌ {error_msg}")
            return False
    
    def fix_app_duplicate_routes(self):
        """Fix duplicate chatbot routes in app.py"""
        logger.info("🔧 Fixing duplicate routes in app.py...")
        
        try:
            # Check main app files
            app_files = ['app.py', 'app/__init__.py']
            
            for app_file in app_files:
                app_path = Path(app_file)
                if not app_path.exists():
                    continue
                
                # Read current content
                with open(app_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Remove duplicate route registrations
                lines = content.split('\n')
                seen_routes = set()
                filtered_lines = []
                
                for line in lines:
                    # Check for blueprint registrations
                    if 'register_blueprint' in line:
                        route_name = line.strip()
                        if route_name not in seen_routes:
                            seen_routes.add(route_name)
                            filtered_lines.append(line)
                        else:
                            logger.info(f"Removed duplicate route: {route_name}")
                    else:
                        filtered_lines.append(line)
                
                # Write back if changes were made
                new_content = '\n'.join(filtered_lines)
                if new_content != content:
                    with open(app_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    self.fixes_applied.append(f"Removed duplicate routes in {app_file}")
                    logger.info(f"✅ Fixed duplicate routes in {app_file}")
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to fix duplicate routes: {e}"
            self.errors_encountered.append(error_msg)
            logger.error(f"❌ {error_msg}")
            return False
    
    def fix_environment_configuration(self):
        """Fix environment configuration issues"""
        logger.info("🔧 Fixing environment configuration...")
        
        try:
            # Check if cricverse.env exists
            env_file = 'cricverse.env' if os.path.exists('cricverse.env') else '.env'
            
            if not os.path.exists(env_file):
                logger.warning("No environment file found, creating from example")
                
                if os.path.exists('.env.example'):
                    shutil.copy('.env.example', '.env')
                    self.fixes_applied.append("Created .env from .env.example")
                    logger.info("✅ Created environment file from example")
                else:
                    logger.warning("No .env.example found to copy from")
                    return False
            
            # Check for placeholder values and warn
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            placeholder_patterns = [
                'your_openai_api_key_here',
                'your_supabase_url_here',
                'your_database_url_here',
                'change-this-to-something-secure'
            ]
            
            issues_found = []
            for pattern in placeholder_patterns:
                if pattern in content:
                    issues_found.append(pattern)
            
            if issues_found:
                logger.warning(f"Found placeholder values in {env_file}: {issues_found}")
                self.errors_encountered.append(f"Placeholder values found in {env_file}")
            else:
                logger.info("✅ No placeholder values found in environment file")
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to fix environment configuration: {e}"
            self.errors_encountered.append(error_msg)
            logger.error(f"❌ {error_msg}")
            return False
    
    def fix_qr_code_api_response(self):
        """Fix QR code API response format"""
        logger.info("🔧 Fixing QR code API response format...")
        
        try:
            # Check app routes for QR code endpoints
            route_files = [
                'app.py',
                'app/__init__.py',
                'app/routes/main.py',
                'app/routes/ticketing.py'
            ]
            
            for route_file in route_files:
                route_path = Path(route_file)
                if not route_path.exists():
                    continue
                
                # Read current content
                with open(route_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Fix QR code response format
                changes_made = False
                
                # Fix ticket QR endpoint
                if "'qr_code':" in content:
                    content = content.replace("'qr_code':", "'qr_code_base64':")
                    changes_made = True
                    logger.info("Fixed ticket QR response format")
                
                # Fix parking QR endpoint
                if '"qr_code":' in content:
                    content = content.replace('"qr_code":', '"qr_code_base64":')
                    changes_made = True
                    logger.info("Fixed parking QR response format")
                
                # Write changes if any were made
                if changes_made:
                    with open(route_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    self.fixes_applied.append(f"Fixed QR code response format in {route_file}")
                    logger.info(f"✅ Fixed QR response format in {route_file}")
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to fix QR code response format: {e}"
            self.errors_encountered.append(error_msg)
            logger.error(f"❌ {error_msg}")
            return False
    
    def cleanup_outdated_files(self):
        """Clean up outdated and duplicate files"""
        logger.info("🔧 Cleaning up outdated files...")
        
        try:
            # Files to potentially remove (based on memories)
            files_to_check = [
                'core.py',  # Duplicate of app.py functionality
                'models.py'  # If enhanced_models.py is working
            ]
            
            removed_files = []
            
            for file_path in files_to_check:
                if os.path.exists(file_path):
                    # Create backup before removal
                    backup_path = f"{file_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    shutil.copy(file_path, backup_path)
                    
                    # Remove original (commented out for safety)
                    # os.remove(file_path)
                    # removed_files.append(file_path)
                    
                    logger.info(f"Created backup: {backup_path} (original kept for safety)")
            
            if removed_files:
                self.fixes_applied.append(f"Cleaned up outdated files: {removed_files}")
                logger.info(f"✅ Cleaned up {len(removed_files)} outdated files")
            else:
                logger.info("No outdated files found to clean up")
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to cleanup outdated files: {e}"
            self.errors_encountered.append(error_msg)
            logger.error(f"❌ {error_msg}")
            return False
    
    def create_missing_init_files(self):
        """Create missing __init__.py files"""
        logger.info("🔧 Creating missing __init__.py files...")
        
        try:
            # Directories that should have __init__.py
            directories_to_check = [
                'app',
                'app/models',
                'app/routes',
                'app/services',
                'tests'
            ]
            
            created_files = []
            
            for directory in directories_to_check:
                dir_path = Path(directory)
                if dir_path.exists() and dir_path.is_dir():
                    init_file = dir_path / '__init__.py'
                    if not init_file.exists():
                        # Create basic __init__.py
                        with open(init_file, 'w', encoding='utf-8') as f:
                            f.write(f'"""CricVerse {directory} module"""\n')
                        
                        created_files.append(str(init_file))
                        logger.info(f"Created {init_file}")
            
            if created_files:
                self.fixes_applied.append(f"Created missing __init__.py files: {created_files}")
                logger.info(f"✅ Created {len(created_files)} missing __init__.py files")
            else:
                logger.info("All required __init__.py files already exist")
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to create missing __init__.py files: {e}"
            self.errors_encountered.append(error_msg)
            logger.error(f"❌ {error_msg}")
            return False
    
    def run_comprehensive_fixes(self):
        """Run all fixes"""
        logger.info("🚀 Starting comprehensive CricVerse fixes...")
        
        start_time = datetime.now()
        
        # List of fixes to apply
        fixes = [
            ('Enhanced Models Metadata Column', self.fix_enhanced_models_metadata_column),
            ('Chatbot Imports', self.fix_chatbot_imports),
            ('Realtime Indentation', self.fix_realtime_indentation),
            ('App Duplicate Routes', self.fix_app_duplicate_routes),
            ('Environment Configuration', self.fix_environment_configuration),
            ('QR Code API Response', self.fix_qr_code_api_response),
            ('Missing Init Files', self.create_missing_init_files),
            ('Cleanup Outdated Files', self.cleanup_outdated_files)
        ]
        
        successful_fixes = 0
        total_fixes = len(fixes)
        
        for fix_name, fix_func in fixes:
            logger.info(f"\n{'='*50}")
            logger.info(f"Applying: {fix_name}")
            logger.info(f"{'='*50}")
            
            try:
                if fix_func():
                    successful_fixes += 1
                    logger.info(f"✅ {fix_name} completed successfully")
                else:
                    logger.warning(f"⚠️ {fix_name} completed with warnings")
            except Exception as e:
                logger.error(f"❌ {fix_name} failed: {e}")
                self.errors_encountered.append(f"{fix_name} failed: {str(e)}")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Generate summary
        summary = {
            'timestamp': end_time.isoformat(),
            'duration_seconds': duration,
            'fixes_attempted': total_fixes,
            'fixes_successful': successful_fixes,
            'success_rate': (successful_fixes / total_fixes) * 100,
            'fixes_applied': self.fixes_applied,
            'errors_encountered': self.errors_encountered
        }
        
        # Save detailed report
        with open('cricverse_fixes_report.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Print summary
        logger.info(f"\n{'='*60}")
        logger.info("COMPREHENSIVE FIXES SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Fixes Applied: {successful_fixes}/{total_fixes} ({(successful_fixes/total_fixes)*100:.1f}%)")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Total Changes: {len(self.fixes_applied)}")
        logger.info(f"Errors: {len(self.errors_encountered)}")
        
        if self.fixes_applied:
            logger.info(f"\n✅ FIXES APPLIED:")
            for i, fix in enumerate(self.fixes_applied, 1):
                logger.info(f"   {i}. {fix}")
        
        if self.errors_encountered:
            logger.info(f"\n❌ ERRORS ENCOUNTERED:")
            for i, error in enumerate(self.errors_encountered, 1):
                logger.info(f"   {i}. {error}")
        
        logger.info(f"\n📊 Detailed report saved to: cricverse_fixes_report.json")
        
        return summary

def main():
    """Main execution"""
    fixer = CricVerseFixer()
    summary = fixer.run_comprehensive_fixes()
    
    # Exit with appropriate code
    success_rate = summary['success_rate']
    if success_rate >= 80:
        logger.info("🎉 Most fixes applied successfully!")
        sys.exit(0)
    elif success_rate >= 60:
        logger.warning("⚠️ Some fixes applied, but issues remain")
        sys.exit(1)
    else:
        logger.error("❌ Critical issues encountered during fixes")
        sys.exit(2)

if __name__ == "__main__":
    main()
