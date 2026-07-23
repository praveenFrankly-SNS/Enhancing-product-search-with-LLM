# =====================================================================
# Product Search Pipeline - Diagnostic & Validation Script
# =====================================================================
# Run this in a Databricks notebook to diagnose silent failures
# %run "./DIAGNOSTIC_SCRIPT"

import sys
from typing import Dict, List, Any
from datetime import datetime

# ANSI Colors for output
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"

def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{BOLD}{BLUE}{'='*70}{RESET}")
    print(f"{BOLD}{BLUE}{text:^70}{RESET}")
    print(f"{BOLD}{BLUE}{'='*70}{RESET}\n")

def print_section(text: str):
    """Print a formatted section"""
    print(f"{BOLD}{YELLOW}{text}{RESET}")
    print(f"{YELLOW}{'-'*70}{RESET}")

def print_success(text: str):
    """Print success message"""
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text: str):
    """Print error message"""
    print(f"{RED}❌ {text}{RESET}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{YELLOW}⚠️  {text}{RESET}")

def print_info(text: str):
    """Print info message"""
    print(f"{BLUE}ℹ️  {text}{RESET}")

# =====================================================================
# DIAGNOSTIC TESTS
# =====================================================================

class PipelineDiagnostics:
    def __init__(self):
        self.results = {}
        self.errors = []
        self.warnings = []
        self.timestamp = datetime.now().isoformat()
    
    def run_all_diagnostics(self, catalog: str = "product_search_dev"):
        """Run all diagnostic tests"""
        print_header("PRODUCT SEARCH PIPELINE DIAGNOSTICS")
        print_info(f"Catalog: {catalog}")
        print_info(f"Timestamp: {self.timestamp}\n")
        
        try:
            self.check_environment()
            self.check_imports()
            self.check_sdk_availability()
            self.check_spark_session()
            self.check_data_structures(catalog)
            self.check_vector_search_setup(catalog)
            self.check_search_capabilities(catalog)
            self.generate_report()
        except Exception as e:
            print_error(f"Diagnostic failed: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def check_environment(self):
        """Check environment and workspace setup"""
        print_section("1. ENVIRONMENT CHECK")
        try:
            import os
            import platform
            
            # Python version
            py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            print_success(f"Python version: {py_version}")
            
            # Platform
            print_success(f"Platform: {platform.platform()}")
            
            # Working directory
            cwd = os.getcwd()
            print_info(f"Working directory: {cwd}")
            
            self.results["environment"] = "✅ OK"
        except Exception as e:
            print_error(f"Environment check failed: {str(e)}")
            self.results["environment"] = f"❌ FAILED: {str(e)}"
            self.errors.append(str(e))
    
    def check_imports(self):
        """Check critical library imports"""
        print_section("2. LIBRARY IMPORTS CHECK")
        
        libraries = [
            ("pyspark", "PySpark"),
            ("pandas", "Pandas"),
            ("numpy", "NumPy"),
            ("logging", "Logging"),
        ]
        
        import_results = {}
        for lib_name, display_name in libraries:
            try:
                __import__(lib_name)
                print_success(f"{display_name} imported successfully")
                import_results[lib_name] = "✅"
            except ImportError as e:
                print_error(f"{display_name} import failed: {str(e)}")
                import_results[lib_name] = f"❌ {str(e)}"
                self.errors.append(f"Import error: {lib_name}")
        
        self.results["imports"] = import_results
    
    def check_sdk_availability(self):
        """Check Vector Search SDK availability"""
        print_section("3. VECTOR SEARCH SDK CHECK")
        
        try:
            from databricks.vector_search.client import VectorSearchClient
            print_success("Vector Search SDK is available")
            self.results["vector_search_sdk"] = "✅ Available"
            
            # Try to initialize client
            try:
                vsc = VectorSearchClient()
                print_success("VectorSearchClient initialized successfully")
                self.results["vector_search_client"] = "✅ Initialized"
            except Exception as e:
                print_warning(f"VectorSearchClient init failed: {str(e)}")
                print_info("This may be expected in non-Databricks environments")
                self.results["vector_search_client"] = f"⚠️  {str(e)}"
                self.warnings.append(str(e))
        
        except ImportError:
            print_error("Vector Search SDK NOT available")
            print_warning("Recommendation: Install with: %pip install databricks-vector-search")
            self.results["vector_search_sdk"] = "❌ Not installed"
            self.warnings.append("Vector Search SDK not installed")
    
    def check_spark_session(self):
        """Check Spark session and configuration"""
        print_section("4. SPARK SESSION CHECK")
        
        try:
            from pyspark.sql import SparkSession
            spark = SparkSession.builder.getOrCreate()
            
            print_success("Spark session active")
            print_info(f"Spark version: {spark.version}")
            print_info(f"App name: {spark.sparkContext.appName}")
            
            # Check catalog support
            try:
                databases = spark.sql("SHOW CATALOGS").collect()
                print_success(f"Found {len(databases)} catalogs")
                self.results["spark_session"] = "✅ OK"
            except Exception as e:
                print_warning(f"Could not list catalogs: {str(e)}")
                self.results["spark_session"] = "✅ OK (partial)"
        
        except Exception as e:
            print_error(f"Spark session check failed: {str(e)}")
            self.results["spark_session"] = f"❌ {str(e)}"
            self.errors.append(str(e))
    
    def check_data_structures(self, catalog: str):
        """Check if data structures exist"""
        print_section("5. DATA STRUCTURES CHECK")
        
        try:
            from pyspark.sql import SparkSession
            spark = SparkSession.builder.getOrCreate()
            
            schemas = ["bronze", "silver", "gold", "operations"]
            tables_found = []
            tables_missing = []
            
            for schema in schemas:
                try:
                    query = f"SHOW TABLES IN `{catalog}`.{schema}"
                    result = spark.sql(query).collect()
                    table_count = len(result)
                    
                    if table_count > 0:
                        print_success(f"Schema '{schema}': {table_count} tables found")
                        tables_found.append((schema, table_count))
                    else:
                        print_warning(f"Schema '{schema}': No tables found")
                        tables_missing.append(schema)
                
                except Exception as e:
                    print_warning(f"Schema '{schema}': Not accessible ({str(e)[:50]}...)")
                    tables_missing.append(schema)
            
            self.results["data_structures"] = {
                "found": tables_found,
                "missing": tables_missing
            }
        
        except Exception as e:
            print_error(f"Data structures check failed: {str(e)}")
            self.results["data_structures"] = f"❌ {str(e)}"
            self.errors.append(str(e))
    
    def check_vector_search_setup(self, catalog: str):
        """Check Vector Search endpoint and index setup"""
        print_section("6. VECTOR SEARCH SETUP CHECK")
        
        try:
            from databricks.vector_search.client import VectorSearchClient
            vsc = VectorSearchClient()
            
            # Check endpoints
            try:
                endpoints = vsc.list_endpoints().get("endpoints", [])
                print_success(f"Found {len(endpoints)} Vector Search endpoint(s)")
                
                for ep in endpoints:
                    ep_name = ep.get("name", "unknown")
                    ep_status = ep.get("endpoint_status", {}).get("state", "unknown")
                    print_info(f"  - {ep_name}: {ep_status}")
                
                self.results["vector_endpoints"] = [ep.get("name") for ep in endpoints]
                
                # Check if shared_vs_endpoint exists
                endpoint_names = [ep.get("name") for ep in endpoints]
                if "shared_vs_endpoint" in endpoint_names:
                    print_success("✅ 'shared_vs_endpoint' found and available")
                    self.results["shared_vs_endpoint"] = "✅ Available"
                else:
                    print_warning("'shared_vs_endpoint' NOT found")
                    self.results["shared_vs_endpoint"] = "⚠️  Not found"
                    self.warnings.append("shared_vs_endpoint not configured")
            
            except Exception as e:
                print_warning(f"Could not list endpoints: {str(e)}")
                self.results["vector_endpoints"] = f"⚠️  {str(e)}"
        
        except ImportError:
            print_warning("Vector Search SDK not available - skipping endpoint check")
            self.results["vector_search_setup"] = "⚠️  SDK not available"
    
    def check_search_capabilities(self, catalog: str):
        """Check search function capabilities"""
        print_section("7. SEARCH CAPABILITIES CHECK")
        
        try:
            # Try to import search functions
            from src.search.search_pipeline import (
                execute_amazon_product_search,
                execute_hybrid_search,
                execute_sql_keyword_search,
                get_vector_index_status
            )
            
            print_success("Search functions imported successfully")
            print_info("Available search modes:")
            print_info("  - execute_amazon_product_search (Vector search)")
            print_info("  - execute_hybrid_search (Vector + Keyword)")
            print_info("  - execute_sql_keyword_search (Fallback)")
            print_info("  - get_vector_index_status (Index monitoring)")
            
            self.results["search_capabilities"] = "✅ Available"
        
        except ImportError as e:
            print_error(f"Search functions import failed: {str(e)}")
            self.results["search_capabilities"] = f"❌ {str(e)}"
            self.errors.append(str(e))
        except Exception as e:
            print_error(f"Search capabilities check failed: {str(e)}")
            self.results["search_capabilities"] = f"❌ {str(e)}"
            self.errors.append(str(e))
    
    def generate_report(self):
        """Generate diagnostic report"""
        print_header("DIAGNOSTIC REPORT SUMMARY")
        
        print_section("Results")
        for key, value in self.results.items():
            if isinstance(value, dict):
                print_info(f"{key}: {value}")
            else:
                print_info(f"{key}: {value}")
        
        if self.errors:
            print_section("Errors Found")
            for i, error in enumerate(self.errors, 1):
                print_error(f"{i}. {error}")
        else:
            print_success("No critical errors found!")
        
        if self.warnings:
            print_section("Warnings")
            for i, warning in enumerate(self.warnings, 1):
                print_warning(f"{i}. {warning}")
        else:
            print_success("No warnings!")
        
        print_section("Recommendations")
        if "Vector Search SDK" in str(self.warnings):
            print_info("1. Install Vector Search SDK:")
            print_info("   %pip install databricks-vector-search")
            print_info("   dbutils.library.restartPython()")
        
        if self.errors:
            print_info("2. Review and fix errors listed above")
            print_info("3. Re-run diagnostics after fixes")
        
        if not self.errors and not self.warnings:
            print_success("✅ Pipeline environment is healthy!")
            print_success("✅ Ready to run end-to-end pipeline")
        
        print(f"\n{BOLD}{BLUE}Report generated at: {self.timestamp}{RESET}\n")

# =====================================================================
# MAIN EXECUTION
# =====================================================================

if __name__ == "__main__":
    diagnostics = PipelineDiagnostics()
    
    # Get catalog from widget or use default
    try:
        catalog = dbutils.widgets.get("catalog")
    except:
        catalog = "product_search_dev"
    
    diagnostics.run_all_diagnostics(catalog)
