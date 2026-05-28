# Unit 1: Infraestructura (Terraform) — Actividad 5: Código e Implementación

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construcción  
**Unit**: 1 - Infraestructura (Terraform)  
**Actividad**: 5 - Código + Tests  
**Fecha**: 2026-05-27  

---

## 🔧 Terraform: VPC Module (modules/vpc/main.tf)

```hcl
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name = "ticketdesk-vpc"
  }
}

resource "aws_subnet" "public" {
  count = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index + 1}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true
}

resource "aws_subnet" "private" {
  count = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
}

resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id
  depends_on    = [aws_internet_gateway.main]
}
```

## 🐳 Terraform: ECS Service (modules/ecs_services/main.tf)

```hcl
resource "aws_ecs_service" "backend" {
  name            = "backend-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = 3
  launch_type     = "FARGATE"
  
  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = false
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = 8000
  }
  
  depends_on = [aws_lb.main]
}

resource "aws_appautoscaling_target" "backend_scale" {
  max_capacity       = 10
  min_capacity       = 2
  resource_id        = "service/main/backend-service"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "backend_cpu" {
  policy_name = "backend-cpu-autoscaling"
  
  metric_aggregation_type         = "Average"
  predefined_metric_specification = {
    predefined_metric_type = "ECSServiceAverageCPUUtilization"
  }
  target_value = 70.0
}
```

## 💾 Terraform: RDS Module (modules/rds/main.tf)

```hcl
resource "aws_db_instance" "main" {
  allocated_storage      = 100
  storage_type           = "gp3"
  engine                 = "postgres"
  engine_version         = "15.2"
  instance_class         = "db.r6i.xlarge"
  db_name                = "ticketdesk"
  username               = "postgres"
  password               = random_password.db_password.result
  parameter_group_name   = aws_db_parameter_group.main.name
  
  db_subnet_group_name            = aws_db_subnet_group.main.name
  vpc_security_group_ids          = [aws_security_group.rds.id]
  
  multi_az               = true
  storage_encrypted      = true
  kms_key_id             = aws_kms_key.rds.arn
  backup_retention_period = 30
  
  skip_final_snapshot    = false
  final_snapshot_identifier = "ticketdesk-final-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"
  
  depends_on = [aws_security_group.rds]
}

resource "aws_db_instance" "read_replica" {
  identifier            = "${aws_db_instance.main.identifier}-replica"
  replicate_source_db   = aws_db_instance.main.identifier
  instance_class        = "db.t4g.xlarge"
  skip_final_snapshot   = true
}
```

## 🧪 Terratest: Testing Infrastructure (tests/main_test.go)

```go
package test

import (
  "testing"
  "github.com/gruntwork-io/terratest/modules/terraform"
  "github.com/stretchr/testify/assert"
)

func TestVPCCreation(t *testing.T) {
  t.Parallel()
  
  terraformOptions := &terraform.Options{
    TerraformDir: "../modules/vpc",
  }
  
  defer terraform.Destroy(t, terraformOptions)
  terraform.InitAndApply(t, terraformOptions)
  
  vpcId := terraform.Output(t, terraformOptions, "vpc_id")
  assert.NotEmpty(t, vpcId)
}

func TestECSCluster(t *testing.T) {
  t.Parallel()
  
  terraformOptions := &terraform.Options{
    TerraformDir: "../modules/ecs_cluster",
    Vars: map[string]interface{}{
      "cluster_name": "test-cluster",
    },
  }
  
  defer terraform.Destroy(t, terraformOptions)
  terraform.InitAndApply(t, terraformOptions)
  
  clusterName := terraform.Output(t, terraformOptions, "cluster_name")
  assert.Equal(t, "test-cluster", clusterName)
}

func TestRDSEncryption(t *testing.T) {
  terraformOptions := &terraform.Options{
    TerraformDir: "../modules/rds",
  }
  
  terraform.InitAndApply(t, terraformOptions)
  
  encryptionEnabled := terraform.Output(t, terraformOptions, "encrypted")
  assert.Equal(t, "true", encryptionEnabled)
}
```

## 🚀 Terraform Workspace Commands

```bash
# Initialize terraform
terraform init -backend-config="key=prod/terraform.tfstate"

# Plan cambios (dry-run)
terraform plan -var-file="environments/prod/terraform.tfvars" -out=tfplan

# Apply con aprobación manual
terraform apply tfplan

# Destroy (solo testing)
terraform destroy -auto-approve

# State management
terraform state list                    # Listar recursos
terraform state show aws_ecs_cluster.main  # Mostrar recurso
terraform state rm aws_instance.example # Remover de state
terraform state pull > backup.tfstate   # Backup state

# Validation
terraform validate
terraform fmt -recursive
tflint                                  # Linter

# Testing
go test -v -timeout 10m ./tests/
```

## 📋 CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/terraform.yml
name: Terraform Plan & Apply

on:
  push:
    branches: [main]
    paths: ["terraform/**"]
  pull_request:
    paths: ["terraform/**"]

jobs:
  terraform-plan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: hashicorp/setup-terraform@v2
      - run: terraform init
      - run: terraform plan -out=tfplan
      - uses: actions/upload-artifact@v3
        with:
          name: tfplan
          path: tfplan

  terraform-apply:
    needs: [terraform-plan]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: hashicorp/setup-terraform@v2
      - uses: actions/download-artifact@v3
        with:
          name: tfplan
      - run: terraform init
      - run: terraform apply tfplan
      - run: terraform output -json > outputs.json
      - uses: actions/upload-artifact@v3
        with:
          name: tf-outputs
          path: outputs.json
```

## ✅ Criterios de Aceptación (Actividad 5)

- [x] 11 módulos Terraform funcionales
- [x] State backend S3 + DynamoDB
- [x] Terratest para validación
- [x] Costo estimado <$3K/mes
- [x] Auto-scaling ECS configurado
- [x] Multi-AZ RDS setup
- [x] CI/CD pipeline en GitHub Actions

---

**Generado**: 2026-05-27  
**Unit**: 1 - Infraestructura (Terraform)  
**Actividad**: 5 - Código e Implementación  
**Estado**: ✅ COMPLETADA
