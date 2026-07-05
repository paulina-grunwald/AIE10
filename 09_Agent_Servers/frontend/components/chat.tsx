"use client";

import { useEffect, useRef, useState } from "react";
import { useStream } from "@langchain/react";
import {
  Bot,
  FileText,
  Loader2,
  Search,
  Send,
  User,
  Wrench,
} from "lucide-react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import {
  getMessageText,
  getToolQuery,
  hostname,
  parseSearchResults,
  splitPassages,
  toolLabel,
} from "@/lib/messages";
import { Markdown } from "@/components/markdown";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "/api";

type StreamMessage = ReturnType<typeof useStream>["messages"][number];

const SUGGESTIONS = [
  "How often should I deworm my cat?",
  "What vaccinations do kittens need?",
  "What are signs of feline dehydration?",
];

function toolIcon(name?: string) {
  if (name === "retrieve_information") return <FileText className="size-3" />;
  if (name?.startsWith("tavily")) return <Search className="size-3" />;
  return <Wrench className="size-3" />;
}

export function Chat({ assistantId }: { assistantId: string }) {
  const stream = useStream({ apiUrl: API_URL, assistantId });
  const { messages, isLoading, error } = stream;

  const [input, setInput] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  // Map each tool result back to the query the agent searched for.
  // Tool result messages carry a tool_call_id; the matching AI message holds
  // the tool_calls with the arguments.
  const queryByToolCallId = new Map<string, string>();
  for (const m of messages) {
    if (m.type !== "ai") continue;
    const calls =
      (m as unknown as { tool_calls?: Array<{ id?: string; args?: unknown }> })
        .tool_calls ?? [];
    for (const call of calls) {
      const query = getToolQuery(call.args);
      if (call.id && query) queryByToolCallId.set(call.id, query);
    }
  }

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, isLoading]);

  const send = (text: string) => {
    const content = text.trim();
    if (!content || isLoading) return;
    stream.submit({ messages: [{ type: "human", content }] });
    setInput("");
  };

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    send(input);
  };

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <ScrollArea className="flex-1">
        <div className="mx-auto flex w-full max-w-3xl flex-col gap-4 px-4 py-6">
          {messages.length === 0 && (
            <div className="mt-10 flex flex-col items-center gap-6 text-center">
              <div className="flex size-14 items-center justify-center rounded-full bg-muted">
                <Bot className="size-7 text-muted-foreground" />
              </div>
              <div className="space-y-1">
                <h2 className="text-lg font-medium">Ask the cat health agent</h2>
                <p className="text-sm text-muted-foreground">
                  Streams from your LangGraph deployment via a secure proxy.
                </p>
              </div>
              <div className="flex flex-wrap justify-center gap-2">
                {SUGGESTIONS.map((s) => (
                  <Button
                    key={s}
                    variant="outline"
                    size="sm"
                    onClick={() => send(s)}
                  >
                    {s}
                  </Button>
                ))}
              </div>
            </div>
          )}

          {messages.map((message, i) => (
            <MessageRow
              key={message.id ?? i}
              message={message}
              query={
                message.type === "tool"
                  ? queryByToolCallId.get(
                      (message as unknown as { tool_call_id?: string })
                        .tool_call_id ?? ""
                    )
                  : undefined
              }
            />
          ))}

          {isLoading && <ThinkingRow />}

          {error != null && (
            <Card className="border-destructive/40">
              <CardContent className="text-sm text-destructive">
                {error instanceof Error ? error.message : "Something went wrong."}
              </CardContent>
            </Card>
          )}

          <div ref={endRef} />
        </div>
      </ScrollArea>

      <div className="border-t bg-background">
        <form
          onSubmit={onSubmit}
          className="mx-auto flex w-full max-w-3xl items-center gap-2 px-4 py-3"
        >
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Message the agent..."
            disabled={isLoading}
            className="h-10"
            autoFocus
          />
          <Button
            type="submit"
            size="lg"
            disabled={isLoading || input.trim().length === 0}
            className="h-10"
          >
            {isLoading ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <Send className="size-4" />
            )}
          </Button>
        </form>
      </div>
    </div>
  );
}

function MessageRow({
  message,
  query,
}: {
  message: StreamMessage;
  query?: string;
}) {
  const isHuman = message.type === "human";
  const isTool = message.type === "tool";
  const text = getMessageText(message.content);
  const toolCalls =
    message.type === "ai"
      ? (message as unknown as {
          tool_calls?: Array<{ name?: string; id?: string }>;
        }).tool_calls ?? []
      : [];

  if (isTool) {
    return <ToolResult name={message.name} text={text} query={query} />;
  }

  return (
    <div
      className={cn(
        "flex w-full items-start gap-3",
        isHuman && "flex-row-reverse"
      )}
    >
      <Avatar>
        <AvatarFallback>
          {isHuman ? (
            <User className="size-4" />
          ) : (
            <Bot className="size-4" />
          )}
        </AvatarFallback>
      </Avatar>

      <div className={cn("flex max-w-[80%] flex-col gap-2", isHuman && "items-end")}>
        {toolCalls.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {toolCalls.map((tc, idx) => (
              <Badge key={tc.id ?? idx} variant="secondary">
                {toolIcon(tc.name)}
                {toolLabel(tc.name)}
              </Badge>
            ))}
          </div>
        )}

        {text && (
          <div
            className={cn(
              "rounded-2xl px-4 py-2.5 text-sm",
              isHuman
                ? "whitespace-pre-wrap bg-primary text-primary-foreground"
                : "bg-muted text-foreground"
            )}
          >
            {isHuman ? text : <Markdown>{text}</Markdown>}
          </div>
        )}
      </div>
    </div>
  );
}

function ToolResult({
  name,
  text,
  query,
}: {
  name?: string;
  text: string;
  query?: string;
}) {
  const searchResults = parseSearchResults(text);
  const passages =
    !searchResults && name === "retrieve_information"
      ? splitPassages(text)
      : null;

  const count = searchResults?.length ?? passages?.length ?? null;

  return (
    <div className="mx-auto w-full max-w-3xl">
      <details className="group rounded-lg border bg-muted/40 text-sm">
        <summary className="flex cursor-pointer list-none items-center gap-2 px-3 py-2 text-muted-foreground">
          {toolIcon(name)}
          <span className="font-medium text-foreground">{toolLabel(name)}</span>
          {query && (
            <span className="truncate text-xs text-muted-foreground">
              &ldquo;{query}&rdquo;
            </span>
          )}
          {count != null && (
            <Badge variant="secondary" className="ml-auto shrink-0">
              {count} {searchResults ? "sources" : "passages"}
            </Badge>
          )}
        </summary>

        <div className="space-y-2 px-3 pb-3">
          {searchResults ? (
            searchResults.map((r, i) => (
              <a
                key={r.url || i}
                href={r.url}
                target="_blank"
                rel="noreferrer"
                className="block rounded-md border bg-background/60 p-2.5 transition-colors hover:bg-background"
              >
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <Search className="size-3 shrink-0" />
                  <span className="truncate">{hostname(r.url)}</span>
                </div>
                <div className="mt-0.5 font-medium text-foreground">
                  {r.title}
                </div>
                {r.content && (
                  <p className="mt-1 line-clamp-3 text-xs text-muted-foreground">
                    {r.content}
                  </p>
                )}
              </a>
            ))
          ) : passages ? (
            passages.map((p, i) => (
              <div
                key={i}
                className="rounded-md border bg-background/60 p-2.5 text-xs"
              >
                <div className="mb-1 flex items-center gap-1.5 text-muted-foreground">
                  <FileText className="size-3 shrink-0" />
                  Passage {i + 1}
                </div>
                <p className="whitespace-pre-wrap text-muted-foreground">{p}</p>
              </div>
            ))
          ) : (
            <pre className="max-h-64 overflow-auto whitespace-pre-wrap text-xs text-muted-foreground">
              {text}
            </pre>
          )}
        </div>
      </details>
    </div>
  );
}

function ThinkingRow() {
  return (
    <div className="flex w-full items-start gap-3">
      <Avatar>
        <AvatarFallback>
          <Bot className="size-4" />
        </AvatarFallback>
      </Avatar>
      <div className="flex items-center gap-2 rounded-2xl bg-muted px-4 py-3 text-sm text-muted-foreground">
        <Loader2 className="size-4 animate-spin" />
        Thinking...
      </div>
    </div>
  );
}
