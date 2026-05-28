# Route53 Module - Outputs

output "app_fqdn" {
  description = "Main application FQDN"
  value       = aws_route53_record.app.fqdn
}

output "www_fqdn" {
  description = "WWW subdomain FQDN"
  value       = aws_route53_record.www.fqdn
}

output "api_fqdn" {
  description = "API subdomain FQDN"
  value       = aws_route53_record.api.fqdn
}

output "app_health_check_id" {
  description = "Application health check ID"
  value       = aws_route53_health_check.app.id
}

output "api_health_check_id" {
  description = "API health check ID"
  value       = aws_route53_health_check.api.id
}

output "hosted_zone_id" {
  description = "Route53 hosted zone ID"
  value       = data.aws_route53_zone.main.zone_id
}

output "nameservers" {
  description = "Route53 nameservers"
  value       = data.aws_route53_zone.main.name_servers
}
