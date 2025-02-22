import { getMatchingPapers } from "@/lib/actions/papers";
import { getVenues } from "@/lib/actions/venues";
import { PaperBrowser, PaperBrowserProps } from "@/components/paper-browser-v2";
import { Box, Card, Container, Skeleton, Stack } from "@mantine/core";
import PaperFilterContainer from "@/components/paper-browser-v2/paper-filter-container";
import { Suspense } from "react";

const getStringList = (value?: string | string[] | undefined) => {
  if (!value) return [];
  return typeof value === "string" ? [value] : value;
};

export default async function PageContainer({
  searchParams,
}: {
  searchParams: Promise<PaperBrowserProps["searchParams"]>;
}) {
  const awaitedSearchParams = await searchParams;
  return (
    <Stack style={{ height: "100%", overflow: "hidden" }}>
      <Suspense
        fallback={
          <>
            <Container w="100%" size="lg">
              <PaperFilterContainer
                venues={[]}
                searchParams={awaitedSearchParams}
                isLoading={true}
              />
            </Container>
            <Box flex={1} style={{ overflow: "auto" }}>
              <Container size="lg">
                <LoadingSkeleton />
              </Container>
            </Box>
          </>
        }
      >
        <Container w="100%" size="lg">
          <PageFilter searchParams={awaitedSearchParams} />
        </Container>
        <Box flex={1} style={{ overflow: "auto" }}>
          <Container size="lg">
            <PageContent searchParams={awaitedSearchParams} />
          </Container>
        </Box>
      </Suspense>
    </Stack>
  );
}

async function PageFilter({
  searchParams,
}: {
  searchParams: PaperBrowserProps["searchParams"];
}) {
  const venues = await getVenues();
  return <PaperFilterContainer venues={venues} searchParams={searchParams} />;
}

async function PageContent({
  searchParams,
}: {
  searchParams: PaperBrowserProps["searchParams"];
}) {
  const papers = await getMatchingPapers({
    search: searchParams.search,
    venue_abbrevs: getStringList(searchParams.venue_abbrevs),
    page: searchParams.page || "1",
    year_min: searchParams.year_min,
    year_max: searchParams.year_max,
    has_code: searchParams.has_code,
  });

  return <PaperBrowser papers={papers} searchParams={searchParams} />;
}

function LoadingSkeleton() {
  return (
    <Stack gap="md" style={{ flex: 1, overflow: "auto" }}>
      {[...Array(5)].map((_, i) => (
        <Card key={i} shadow="sm" padding="lg" radius="md" withBorder>
          <Stack>
            <Skeleton height={24} width="60%" />
            <Skeleton height={16} width="40%" />
            <Skeleton height={60} />
            <Skeleton height={20} width={80} />
          </Stack>
        </Card>
      ))}
    </Stack>
  );
}
