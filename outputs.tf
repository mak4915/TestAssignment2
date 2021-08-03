output "vpc_id" {
  value = aws_vpc.myvpc.id
}
output "elb_dns" {
  value = aws_elb.my_elb.dns_name
}