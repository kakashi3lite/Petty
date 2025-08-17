class PetPlan {
  final Map<String, dynamic> json;
  PetPlan(this.json);
  List<String> get alerts => (json['health_alerts'] as List<dynamic>? ?? []).cast<String>();
}
