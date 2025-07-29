resource "aws_vpc" "main" {
  cidr_block           = "10.1.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-vpc" })
  )
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-igw" })
  )
}

#####################################################
# Public Subnets - Inbound/Outbound Internet Access #
#####################################################
resource "aws_subnet" "public_a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.1.1.0/24"
  map_public_ip_on_launch = true
  availability_zone       = "${data.aws_region.current.name}a"

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-public-a" })
  )
}

resource "aws_route_table" "public_a" {
  vpc_id = aws_vpc.main.id
  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-public-a-rt" })
  )
}

resource "aws_route_table_association" "public_a" {
  subnet_id      = aws_subnet.public_a.id
  route_table_id = aws_route_table.public_a.id
}

resource "aws_route" "public_internet_access_a" {
  route_table_id         = aws_route_table.public_a.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.main.id
}

resource "aws_eip" "public_a" {
  domain = "vpc"
  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-public-a-eip" })
  )
}

resource "aws_nat_gateway" "public_a" {
  subnet_id     = aws_subnet.public_a.id
  allocation_id = aws_eip.public_a.id
  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-public-a-nat" })
  )
}

resource "aws_subnet" "public_b" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.1.2.0/24"
  map_public_ip_on_launch = true
  availability_zone       = "${data.aws_region.current.name}b"

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-public-b" })
  )
}

resource "aws_route_table" "public_b" {
  vpc_id = aws_vpc.main.id
  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-public-b-rt" })
  )
}

resource "aws_route_table_association" "public_b" {
  subnet_id      = aws_subnet.public_b.id
  route_table_id = aws_route_table.public_b.id
}

resource "aws_route" "public_internet_access_b" {
  route_table_id         = aws_route_table.public_b.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.main.id
}

resource "aws_eip" "public_b" {
  domain = "vpc"
  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-public-b-eip" })
  )
}

resource "aws_nat_gateway" "public_b" {
  subnet_id     = aws_subnet.public_b.id
  allocation_id = aws_eip.public_b.id
  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-public-b-nat" })
  )
}

#####################################################
# Public Subnets - Outbound Internet Access only    #
#####################################################

resource "aws_subnet" "private_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.1.10.0/24"
  availability_zone = "${data.aws_region.current.name}a"

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-private-a" })
  )
}

resource "aws_route_table" "private_a" {
  vpc_id = aws_vpc.main.id
  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-private-a-rt" })
  )
}

resource "aws_route_table_association" "private_a" {
  subnet_id      = aws_subnet.private_a.id
  route_table_id = aws_route_table.private_a.id
}

resource "aws_route" "private_a_internet_out" {
  route_table_id         = aws_route_table.private_a.id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.public_a.id
}

resource "aws_subnet" "private_b" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.1.11.0/24"
  availability_zone = "${data.aws_region.current.name}b"

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-private-b" })
  )
}

resource "aws_route_table" "private_b" {
  vpc_id = aws_vpc.main.id
  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-private-b-rt" })
  )
}

resource "aws_route_table_association" "private_b" {
  subnet_id      = aws_subnet.private_b.id
  route_table_id = aws_route_table.private_b.id
}

resource "aws_route" "private_b_internet_out" {
  route_table_id         = aws_route_table.private_b.id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.public_b.id
}

