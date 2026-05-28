import { DynamoDBClient, DescribeTableCommand } from "@aws-sdk/client-dynamodb";
import {
  DynamoDBDocumentClient,
  GetCommand,
  PutCommand,
  QueryCommand,
  TransactWriteCommand,
  BatchWriteCommand,
  DeleteCommand
} from "@aws-sdk/lib-dynamodb";
import type { ParticipantRecord, SessionRecord } from "../types";

const tableName = (): string => {
  const name = process.env.DYNAMODB_TABLE_NAME;
  if (!name) throw new Error("DYNAMODB_TABLE_NAME env var is required");
  return name;
};

const raw = new DynamoDBClient({});
const doc = DynamoDBDocumentClient.from(raw, {
  marshallOptions: { removeUndefinedValues: true, convertEmptyValues: false }
});

export async function describeTable(): Promise<{ status: string }> {
  const res = await raw.send(new DescribeTableCommand({ TableName: tableName() }));
  return { status: res.Table?.TableStatus ?? "UNKNOWN" };
}

export async function getSession(sessionCode: string): Promise<SessionRecord | null> {
  const res = await doc.send(
    new GetCommand({
      TableName: tableName(),
      Key: { PK: `SESSION#${sessionCode}`, SK: "METADATA" }
    })
  );
  return (res.Item as SessionRecord | undefined) ?? null;
}

export async function putSession(sessionCode: string): Promise<SessionRecord> {
  const record: SessionRecord = {
    PK: `SESSION#${sessionCode}`,
    SK: "METADATA",
    sessionCode,
    createdAt: new Date().toISOString()
  };
  await doc.send(new PutCommand({ TableName: tableName(), Item: record }));
  return record;
}

export async function getParticipant(
  sessionCode: string,
  participantId: string
): Promise<ParticipantRecord | null> {
  const res = await doc.send(
    new GetCommand({
      TableName: tableName(),
      Key: { PK: `SESSION#${sessionCode}`, SK: `PARTICIPANT#${participantId}` }
    })
  );
  return (res.Item as ParticipantRecord | undefined) ?? null;
}

export async function putParticipant(record: ParticipantRecord): Promise<void> {
  await doc.send(new PutCommand({ TableName: tableName(), Item: record }));
}

// Troubleshooting #26: don't annotate the response type — DocumentClient returns
// Record<string, any>[] which can't be narrowed in the variable declaration.
// Cast at the use site instead.
export async function queryParticipants(sessionCode: string): Promise<ParticipantRecord[]> {
  const items: ParticipantRecord[] = [];
  let lastKey: Record<string, unknown> | undefined;
  do {
    const res = await doc.send(
      new QueryCommand({
        TableName: tableName(),
        KeyConditionExpression: "PK = :pk AND begins_with(SK, :sk)",
        ExpressionAttributeValues: {
          ":pk": `SESSION#${sessionCode}`,
          ":sk": "PARTICIPANT#"
        },
        ExclusiveStartKey: lastKey
      })
    );
    items.push(...((res.Items as ParticipantRecord[] | undefined) ?? []));
    lastKey = res.LastEvaluatedKey;
  } while (lastKey);
  return items;
}

export async function incrementSkillLike(params: {
  sessionCode: string;
  voterId: string;
  targetParticipantId: string;
  skillId: string;
  skillIndex: number;
}): Promise<{ alreadyVoted: boolean }> {
  const tname = tableName();
  const voteSK = `${params.voterId}#${params.targetParticipantId}#${params.skillId}`;
  try {
    await doc.send(
      new TransactWriteCommand({
        TransactItems: [
          {
            Put: {
              TableName: tname,
              Item: { PK: `VOTE#${params.sessionCode}`, SK: voteSK },
              ConditionExpression: "attribute_not_exists(PK)"
            }
          },
          {
            Update: {
              TableName: tname,
              Key: {
                PK: `SESSION#${params.sessionCode}`,
                SK: `PARTICIPANT#${params.targetParticipantId}`
              },
              UpdateExpression: `SET totalLikes = if_not_exists(totalLikes, :z) + :one, skills[${params.skillIndex}].likeCount = if_not_exists(skills[${params.skillIndex}].likeCount, :z) + :one`,
              ConditionExpression: "attribute_exists(PK)",
              ExpressionAttributeValues: { ":z": 0, ":one": 1 }
            }
          }
        ]
      })
    );
    return { alreadyVoted: false };
  } catch (err: unknown) {
    const name = (err as { name?: string }).name;
    if (
      name === "TransactionCanceledException" ||
      name === "ConditionalCheckFailedException"
    ) {
      return { alreadyVoted: true };
    }
    throw err;
  }
}

export async function batchDeleteSession(sessionCode: string): Promise<number> {
  const tname = tableName();
  let deleted = 0;
  const queries = [
    {
      KeyConditionExpression: "PK = :pk",
      ExpressionAttributeValues: { ":pk": `SESSION#${sessionCode}` }
    },
    {
      KeyConditionExpression: "PK = :pk",
      ExpressionAttributeValues: { ":pk": `VOTE#${sessionCode}` }
    }
  ];

  for (const q of queries) {
    let lastKey: Record<string, unknown> | undefined;
    do {
      const res = await doc.send(
        new QueryCommand({
          TableName: tname,
          KeyConditionExpression: q.KeyConditionExpression,
          ExpressionAttributeValues: q.ExpressionAttributeValues,
          ExclusiveStartKey: lastKey
        })
      );
      const items = (res.Items ?? []) as Array<{ PK: string; SK: string }>;
      for (let i = 0; i < items.length; i += 25) {
        const chunk = items.slice(i, i + 25);
        await doc.send(
          new BatchWriteCommand({
            RequestItems: {
              [tname]: chunk.map((it) => ({ DeleteRequest: { Key: { PK: it.PK, SK: it.SK } } }))
            }
          })
        );
        deleted += chunk.length;
      }
      lastKey = res.LastEvaluatedKey;
    } while (lastKey);
  }
  return deleted;
}

export async function deleteSessionMetadata(sessionCode: string): Promise<void> {
  await doc.send(
    new DeleteCommand({
      TableName: tableName(),
      Key: { PK: `SESSION#${sessionCode}`, SK: "METADATA" }
    })
  );
}
