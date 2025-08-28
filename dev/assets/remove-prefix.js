// Remove TransComp. prefix from function signatures
document.addEventListener('DOMContentLoaded', function() {
    // Find all function signature elements
    const signatures = document.querySelectorAll('.docstring-binding code');
    
    signatures.forEach(function(element) {
        if (element.textContent.startsWith('TransComp.')) {
            element.textContent = element.textContent.replace('TransComp.', '');
        }
    });
    
    // Also handle any other elements that might contain the prefix
    const allCodeElements = document.querySelectorAll('code');
    allCodeElements.forEach(function(element) {
        if (element.textContent.startsWith('TransComp.')) {
            // Only replace if it's at the beginning and followed by a function name
            element.textContent = element.textContent.replace(/^TransComp\.(\w+)/, '$1');
        }
    });
});
