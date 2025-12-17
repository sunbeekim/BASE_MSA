package com.example.llm.summary.repository;

import com.example.llm.summary.entity.Summary;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface SummaryRepository extends JpaRepository<Summary, Long> {
    
    Optional<Summary> findByCallkey(String callkey);
    
    boolean existsByCallkey(String callkey);
}

