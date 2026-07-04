// Global function to fetch and display tasks from MongoDB
// Attached to window so it can be called directly from terminal.js
window.loadTasks = async function() {
    try {
        // Fetch task data from the FastAPI backend
        const response = await fetch('http://127.0.0.1:8000/api/get-tasks');
        const data = await response.json();
        
        const taskListUl = document.getElementById('active-tasks-ul');
        if (!taskListUl) return; // Prevent errors if the element is not found in the DOM
        
        taskListUl.innerHTML = ''; // Clear default dummy tasks

        if (data.tasks && data.tasks.length > 0) {
            data.tasks.forEach(t => {
                // If status is pending, show cyan, if done show green
                let statusColor = t.status === 'pending' ? 'text-cyan' : 'text-green';
                let statusText = t.status === 'pending' ? '[WAITING]' : '[OK]';
                
                // Append the task to the list
                taskListUl.innerHTML += `<li>> ${t.task} <span class="${statusColor}">${statusText}</span></li>`;
            });
        } else {
            // Display message if no tasks exist
            taskListUl.innerHTML = '<li class="text-muted">> No active tasks in database.</li>';
        }
    } catch (error) {
        // Log errors to the console if fetching fails
        console.error("Failed to load tasks:", error);
    }
}

// Load tasks and conversations as soon as the HUD (window) starts
window.onload = () => {
    window.loadTasks();
    
    // Load chat sessions into the left panel
    if (typeof window.loadConversations === 'function') {
        window.loadConversations();
    }
};