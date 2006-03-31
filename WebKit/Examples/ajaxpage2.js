/*
	Extended Ajax Javascript functions used by AjaxPage.

	Implements a polling mechanism to prevent server timeouts.

	Written by John Dickinson based on ideas from
	Apple developer code (developer.apple.com)
	and Nevow 0.4.1 (www.nevow.org).
	Minor changes by Christoph Zwerschke.
*/

var server_response;
var dying = false;

function openResponseConnection(count)
{
	if (!server_response) {
		server_response = createRequest();
	}
	if (server_response) {
		server_response.onreadystatechange = processResponse;
		var loc = document.location.toString();
		if (loc.indexOf('?') != -1) {
			loc = loc.substr(0, loc.indexOf('?'));
		}
		server_response.open("GET", loc+"?_action_=ajax_response&req_count="+count.toString(), true);
		server_response.send(null);
	}
}

function processResponse()
{
	var wait = (3 + Math.random() * 5); // 3 - 8 seconds
	if (server_response.readyState == 4) {
		if (server_response.status == 200) {
			try {
				eval(server_response.responseText);
			} catch(e) {
				; // ignore errors
			}
			if (!dying) {
				request_count += 1;
				// reopen the response connection after a wait period
				setTimeout("openResponseConnection(request_count)", wait*1000);
			}
		}
	}
}

function shutdown()
{
	if (server_response) {
		server_response.abort();
	}
	dying = true;
}

var userAgent = navigator.userAgent.toLowerCase()
if (userAgent.indexOf("msie") != -1) {
	// IE specific
	window.attachEvent("onbeforeunload", shutdown)
} else if (document.implementation && document.implementation.createDocument) {
	// Mozilla specific (onbeforeunload is in v1.7+ only)
	window.addEventListener("beforeunload", shutdown, false)
}

// Open initial connection back to server:
openResponseConnection(request_count);
