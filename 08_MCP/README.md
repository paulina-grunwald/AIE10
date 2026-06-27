<p align="center" draggable="false"><img src="https://github.com/AI-Maker-Space/LLM-Dev-101/assets/37101144/d1343317-fa2f-41e1-8af1-1dbb18399719"
     width="200px"
     height="auto"/>
</p>

<h1 align="center" id="heading">Session 8: Model Context Protocol (MCP)</h1>

### [Quicklinks]()

| Session Sheet                                                                                                              | Recording                                                                                                                                                   | Slides                                                 | Repo          | Homework                                                    | Feedback                                             |
| :------------------------------------------------------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------- | :----------------------------------------------------- | :------------ | :---------------------------------------------------------- | :--------------------------------------------------- |
| [Session 8: MCP](https://github.com/AI-Maker-Space/The-AI-Engineering-Certification-v1.0/tree/main/00_Docs/Modules/08_MCP) | [Recording!](https://us02web.zoom.us/rec/share/rqw5I5hwbOOHy8TrGjnu0IjDJi53ykHb0k897jYfyHqZpgRhUuFP4A18d4NrcEKS.18sNk6Do9XwyaVUy) <br> passcode: `E56&^V+8` | [Session 8 Slides](https://canva.link/k8cixqgkfeghdsn) | You are here! | [Session 8 Assignment](https://forms.gle/TcjjChq38ydMjuqn8) | [Feedback 6/25](https://forms.gle/DvcWDgBXatBWCXqi7) |

## Useful Resources

**MCP (Model Context Protocol)**

- [MCP Official Docs](https://modelcontextprotocol.io/) — Spec, tutorials, and guides
- [MCP-UI](https://mcpui.dev/) — Official standard for interactive UI in MCP
- [MCP Auth Guide (Auth0)](https://auth0.com/blog/mcp-specs-update-all-about-auth/) — Deep dive into MCP auth spec updates

## Main Assignment

In this session, you will build an MCP server with OAuth authentication — a cat
shop application that exposes tools for browsing products, managing a cart, and
checking out.

The main entry point is:

```text
server.py
```

The server implementation lives in:

```text
app/
```

Available MCP tools:

- `list_products`
- `get_product`
- `add_to_cart`
- `view_cart`
- `remove_from_cart`
- `checkout`

## Setup

From this folder:

```bash
uv sync
```

Copy the example env file and fill in your OpenAI API key:

```bash
cp .env.example .env
```

## Running the MCP Server

Run the server locally:

```bash
uv run server.py
```

The server starts on `http://localhost:8000`.

### Expose the server with ngrok

In a separate terminal, start an ngrok tunnel:

```bash
ngrok http 8000
```

Copy the ngrok forwarding URL (e.g. `https://xxxx-xx-xx-xx-xx.ngrok-free.app`) and
restart the server with it:

```bash
ISSUER_URL=https://xxxx-xx-xx-xx-xx.ngrok-free.app uv run server.py
```

> **Note:** The `ISSUER_URL` must match the public URL clients use to reach the
> server, otherwise OAuth authentication will fail.

## Outline

### Breakout Room #1

- Set up the MCP server with OAuth and the product database
- Explore the MCP tools: `list_products`, `get_product`, `add_to_cart`, `view_cart`, `remove_from_cart`, `checkout`

### Breakout Room #2

- Connect an MCP client to the server
- Build an end-to-end interaction flow using the MCP tools

## Ship

The completed MCP server and client integration!

### Deliverables

- A short Loom of either:
  - the MCP server you built and a demo of the client interacting with it; or
  - the notebook you created for the Advanced Build

## Share

Make a social media post about your final application!

### Deliverables

- Make a post on any social media platform about what you built!

Here's a template to get you started:

```
🚀 Exciting News! 🚀

I am thrilled to announce that I have just built and shipped an MCP server with OAuth authentication! 🎉🤖

🔍 Three Key Takeaways:
1️⃣
2️⃣
3️⃣

Let's continue pushing the boundaries of what's possible in the world of AI and tool integration. Here's to many more innovations! 🚀
Shout out to @AIMakerspace !

#MCP #ModelContextProtocol #OAuth #Innovation #AI #TechMilestone

Feel free to reach out if you're curious or would like to collaborate on similar projects! 🤝🔥
```

## Submitting Your Homework

Follow these steps to prepare and submit your homework assignment:

1. Review the MCP server code in `server.py` and the `app/` directory
2. Run the MCP server locally using `uv run server.py`
3. Connect to the server using an MCP client (e.g., Claude Desktop, or a custom client)
4. Test all available tools: browsing products, adding to cart, viewing cart, removing items, and checkout
5. Record a Loom video reviewing what you have learned from this session

## Questions

### Question #1

Why is OAuth important for MCP servers, and what security considerations should you keep in mind when exposing tools to AI clients?

#### Answer

OAuth is important for MCP servers because it provides secure authentication using an access token and a refresh token, so only authenticated users can call our MCP tools. The user's actual credentials are never shared with the AI client; the client only receives a scoped, short-lived token that can expire or be revoked.
OAuth also handles authorization through scopes (our client requests "read write" access), so an AI client only gets the permissions it needs instead of full control. It also allows the server to verify identity for each request, which is how tools know which user is making a request and keep user context separate (e.g one user is not able to add products to other user's cart).

I would keep the following considerations in mind when exposing tools to AI clinets:

- rate limiting, to lower the chance of DDoS and to avoid consuming too many AI tokens and racking up cost,
- observability and audit logging - which user called which tool
- HTTPS only so tokens are protected in transit, short-lived access tokens, and refresh token rotation
- user input sanitization preventing prompt injections

### Question #2

What is Streamable HTTP transport in MCP, and why might you expose a server publicly with OAuth instead of using a local stdio connection?

#### Answer

Streamable HTTP is the standard transport protocol for connecting remote Model Context Protocol (MCP) server. It is the transport used to connect a client to a remote MCP server over the network. The server exposes a single HTTP endpoint (for example /mcp) that supports both POST and GET. The client sends each JSON-RPC message as an HTTP POST. Server can reply in one of two ways:

- single JSON response (application/json)
- it can open a SSE (Server-Sent Events) stream (text/event-stream) when it needs to send multiple messages or stream progress back (SSE is optional and is not required to use in every call).

Mcp-Session-Id is an HTTP header used for session management in the Streamable HTTP transport. When a connection drops, the client issues an HTTP GET to the MCP endpoint including Last-Event-ID set to the last event ID it received. That's how interrupted connections can be resumed.

Stdio connection is used only for local servers as a local subprocess on the same machine, so it can't be shared and there's no network identity to authenticate (simpler, no auth needed). You would have to expose a server publicly over Streamable HTTP when you want to host it once and let multiple users and clients reach it over the internet. In that case you should use OAuth which gives you secure connection and scoped tokens and a verified per-user identity.

## Activity 1: Extend the MCP Server

Add at least one new tool to the cat shop MCP server (e.g., `search_products`, `update_cart_quantity`, or `get_order_history`). Ensure the new tool integrates properly with the existing database and OAuth authentication. Demo the new tool through an MCP client and include it in your Loom video.

## Advanced Activity: Build a Custom MCP Client

Build a custom MCP client that connects to the cat shop server over Streamable HTTP, authenticates via OAuth, and orchestrates a multi-step shopping flow (browse → add to cart → checkout). Compare the developer experience of MCP-based tool integration vs. traditional REST API calls.

Include your findings and a demo in your Loom video.
